import numpy as np
import pytest
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.ai import embedding


class DummyModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def embed_content(self, *, model, contents, config):
        self.calls.append((model, contents, config))
        if not self._responses:
            raise AssertionError("Unexpected embed_content call")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class DummyClient:
    def __init__(self, responses):
        self.models = DummyModels(responses)


def test_resolve_api_key_validation(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(embedding.EmbeddingError):
        embedding._resolve_api_key(None)

    assert embedding._resolve_api_key("explicit-key") == "explicit-key"
    monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
    assert embedding._resolve_api_key(None) == "env-key"


@pytest.mark.parametrize(
    "vector,expected",
    [([3.0, 4.0], np.array([0.6, 0.8], dtype=np.float32)), ([0.0, 0.0], np.array([0.0, 0.0], dtype=np.float32))],
)
def test_normalize_vector(vector, expected):
    out = embedding._normalize_vector(vector)
    np.testing.assert_allclose(out, expected)


def test_perform_embedding_requests_success(monkeypatch):
    response = genai_types.EmbedContentResponse(
        embeddings=[genai_types.ContentEmbedding(values=[3.0, 4.0])]
    )
    client = DummyClient([response])
    monkeypatch.setattr(embedding, "_CLIENT_CACHE", {})
    monkeypatch.setattr(embedding, "_get_client", lambda _: client)
    requests_batch = [embedding._EmbeddingRequest(text="hello", task_type="query")]
    vectors = embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert len(vectors) == 1
    assert float(np.linalg.norm(vectors[0])) == pytest.approx(1.0)
    assert client.models.calls[0][1] == ["hello"]
    assert client.models.calls[0][2].task_type == "query"


def test_perform_embedding_requests_uses_fixed_dimension(monkeypatch):
    response = genai_types.EmbedContentResponse(
        embeddings=[genai_types.ContentEmbedding(values=[3.0, 4.0])]
    )
    client = DummyClient([response])
    monkeypatch.setattr(embedding, "_CLIENT_CACHE", {})
    monkeypatch.setattr(embedding, "_get_client", lambda _: client)
    requests_batch = [embedding._EmbeddingRequest(text="hello", task_type="query")]
    embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    config = client.models.calls[0][2]
    assert getattr(config, "output_dimensionality", None) == 768


def test_perform_embedding_requests_http_error(monkeypatch):
    client = DummyClient([genai_errors.APIError(500, {"error": {"message": "failed"}})])
    monkeypatch.setattr(embedding, "_CLIENT_CACHE", {})
    monkeypatch.setattr(embedding, "_get_client", lambda _: client)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "Embedding API error" in str(exc.value)


def test_perform_embedding_requests_missing_vectors(monkeypatch):
    response = genai_types.EmbedContentResponse(embeddings=[])
    client = DummyClient([response])
    monkeypatch.setattr(embedding, "_CLIENT_CACHE", {})
    monkeypatch.setattr(embedding, "_get_client", lambda _: client)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "missing expected vectors" in str(exc.value)


def test_perform_embedding_requests_invalid_values(monkeypatch):
    response = genai_types.EmbedContentResponse(
        embeddings=[genai_types.ContentEmbedding(values=None)]
    )
    client = DummyClient([response])
    monkeypatch.setattr(embedding, "_CLIENT_CACHE", {})
    monkeypatch.setattr(embedding, "_get_client", lambda _: client)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "empty vector" in str(exc.value)


def test_embed_documents_batches(monkeypatch):
    vectors_returned = []

    def fake_perform(batch, api_key):
        vectors_returned.append(len(batch))
        return [np.ones(3, dtype=np.float32) for _ in batch]

    monkeypatch.setattr(embedding, "_perform_embedding_requests", fake_perform)
    monkeypatch.setenv("GOOGLE_API_KEY", "batch-key")
    texts = [f"text-{i}" for i in range(embedding.BATCH_SIZE + 3)]
    vectors = embedding.embed_documents(texts)
    assert len(vectors) == len(texts)
    assert vectors_returned == [embedding.BATCH_SIZE, 3]


def test_embed_query_requires_vector(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "query-key")
    monkeypatch.setattr(embedding, "_perform_embedding_requests", lambda batch, api_key: [])
    with pytest.raises(embedding.EmbeddingError):
        embedding.embed_query("question")


def test_embed_query_success(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "query-key")

    def fake_perform(batch, api_key):
        assert len(batch) == 1
        return [np.array([1.0, 0.0], dtype=np.float32)]

    monkeypatch.setattr(embedding, "_perform_embedding_requests", fake_perform)
    vector = embedding.embed_query("question")
    np.testing.assert_allclose(vector, np.array([1.0, 0.0], dtype=np.float32))


def test_embed_no_texts_returns_empty(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "query-key")
    result = embedding.embed_documents([])
    assert result == []
