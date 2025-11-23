import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app import rag_loader
from app.ai import EmbeddingError

pytest.importorskip("pyarrow", reason="pyarrow is required for parquet-related tests")


class StubRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def setex(self, key, ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


@pytest.fixture
def parquet_path(tmp_path):
    data = {
        "doc_path": ["doc1", "doc2"],
        "chunk_index": [0, 1],
        "text": ["hello world", "goodbye"],
        "embedding": [[1.0, 0.0], [0.0, 1.0]],
        "meta": [json.dumps({"source": "a"}), json.dumps({"source": "b"})],
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "vectors.parquet"
    df.to_parquet(file_path, index=False)
    return file_path


def setup_module(module):
    rag_loader._clear_cache()
    rag_loader._FAISS_AVAILABLE = False
    rag_loader._FAISS_UNAVAILABLE_WARNED = False


def teardown_module(module):
    rag_loader._clear_cache()


def test_load_vectors_success(parquet_path):
    vectors = rag_loader.load_vectors(parquet_path)
    assert len(vectors) == 2
    assert vectors[0]["idx"] == 0
    assert np.allclose(vectors[0]["embedding"], np.array([1.0, 0.0], dtype=np.float32))


def test_load_vectors_missing_columns(tmp_path):
    df = pd.DataFrame({"doc_path": ["doc1"], "chunk_index": [0], "text": ["x"]})
    file_path = tmp_path / "bad.parquet"
    df.to_parquet(file_path, index=False)
    with pytest.raises(ValueError):
        rag_loader.load_vectors(file_path)


def test_ensure_vectors_uses_disk_and_redis(monkeypatch, parquet_path):
    redis = StubRedis()
    monkeypatch.setattr(rag_loader, "_get_redis_client", lambda: redis)
    monkeypatch.setattr(rag_loader, "_attempt_git_lfs_pull", lambda: None)
    rag_loader._clear_cache()

    vectors = rag_loader.ensure_vectors(parquet_path)
    assert len(vectors) == 2
    cached_payload = redis.store.get(rag_loader._REDIS_CACHE_KEY)
    assert cached_payload is not None

    cached_path = Path(parquet_path)
    cached_path.unlink()
    rag_loader._clear_cache()

    vectors_from_cache = rag_loader.ensure_vectors(parquet_path)
    assert len(vectors_from_cache) == 2


def test_linear_search_returns_ranked_results():
    rag_loader._clear_cache()
    vectors = [
        {"text": "alpha", "doc": "doc", "idx": 0, "meta": {}, "embedding": np.array([1.0, 0.0], dtype=np.float32)},
        {"text": "beta", "doc": "doc", "idx": 1, "meta": {}, "embedding": np.array([0.0, 1.0], dtype=np.float32)},
    ]
    rag_loader._EMBEDDING_MATRIX = np.vstack([v["embedding"] for v in vectors])
    results = rag_loader._linear_search(np.array([1.0, 0.0], dtype=np.float32), vectors, top_k=1, min_sim=0.1)
    assert len(results) == 1
    assert results[0]["text"] == "alpha"


def test_rag_query_handles_embed_error(monkeypatch):
    rag_loader._clear_cache()
    rag_loader._EMBEDDING_MATRIX = np.empty((0, 0), dtype=np.float32)
    monkeypatch.setattr(rag_loader, "ensure_vectors", lambda: [{"embedding": np.array([1.0])}])
    monkeypatch.setattr(rag_loader, "embed_query", lambda *args, **kwargs: (_ for _ in ()).throw(EmbeddingError("bad")))
    assert rag_loader.rag_query("test") == []


def test_rag_query_linear_search(monkeypatch):
    vectors = [
        {"text": "alpha", "doc": "doc", "idx": 0, "meta": {}, "embedding": np.array([1.0, 0.0], dtype=np.float32)},
        {"text": "beta", "doc": "doc", "idx": 1, "meta": {}, "embedding": np.array([0.0, 1.0], dtype=np.float32)},
    ]
    rag_loader._clear_cache()
    rag_loader._EMBEDDING_MATRIX = np.vstack([v["embedding"] for v in vectors])
    monkeypatch.setattr(rag_loader, "ensure_vectors", lambda: vectors)
    monkeypatch.setattr(rag_loader, "embed_query", lambda *args, **kwargs: np.array([1.0, 0.0], dtype=np.float32))
    results = rag_loader.rag_query("hello", top_k=2, min_sim=0.1)
    assert [item["text"] for item in results] == ["alpha"]


def test_rag_query_empty_or_no_vectors(monkeypatch):
    rag_loader._clear_cache()
    assert rag_loader.rag_query("") == []
    monkeypatch.setattr(rag_loader, "ensure_vectors", lambda: [])
    assert rag_loader.rag_query("hello") == []


def test_ensure_vectors_missing_file_triggers_git_lfs(monkeypatch, tmp_path, caplog):
    rag_loader._clear_cache()
    caplog.set_level("WARNING")
    invoked = {"count": 0}

    def fake_lfs_pull():
        invoked["count"] += 1

    monkeypatch.setattr(rag_loader, "_get_redis_client", lambda: None)
    monkeypatch.setattr(rag_loader, "_attempt_git_lfs_pull", fake_lfs_pull)

    missing_path = tmp_path / "missing.parquet"
    result = rag_loader.ensure_vectors(missing_path)

    assert result == []
    assert invoked["count"] == 1
    status = rag_loader.get_status()
    assert status["available"] is False
    assert "RAG 檔案遺失" in status["message"]


def test_rag_status_updates_on_invalid_file(monkeypatch, tmp_path, caplog):
    rag_loader._clear_cache()
    caplog.set_level("ERROR")
    monkeypatch.setattr(rag_loader, "_get_redis_client", lambda: None)
    monkeypatch.setattr(rag_loader, "_attempt_git_lfs_pull", lambda: None)

    bad_path = tmp_path / "broken.parquet"
    bad_path.write_text("not parquet content", encoding="utf-8")

    rag_loader.ensure_vectors(bad_path)
    status = rag_loader.get_status()
    assert status["available"] is False
    assert "無法載入 RAG 檔案" in status["message"]
    assert status["detail"]


def test_rag_status_reflects_success(parquet_path, monkeypatch):
    rag_loader._clear_cache()
    monkeypatch.setattr(rag_loader, "_get_redis_client", lambda: None)
    monkeypatch.setattr(rag_loader, "_attempt_git_lfs_pull", lambda: None)

    rag_loader.ensure_vectors(parquet_path)
    status = rag_loader.get_status()
    assert status["available"] is True
    assert "載入完成" in status["message"]
