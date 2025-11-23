"""Lightweight vector store for Retrieval-Augmented Generation lookups."""
from __future__ import annotations

import base64
import io
import json
import logging
import math
import os
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from flask import current_app, has_app_context

from .ai import EmbeddingError, embed_query

try:  # pragma: no cover - import tested indirectly via search path
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency fallback
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

def _detect_repo_root() -> Path:
    current = Path(__file__).resolve()
    candidates = list(current.parents)
    for candidate in candidates:
        docs_path = candidate / "docs"
        if (docs_path / "rag_vectors").exists():
            return candidate
    return candidates[1] if len(candidates) > 1 else current.parent


_REPO_ROOT = _detect_repo_root()
_DEFAULT_VECTOR_PATH = _REPO_ROOT / "docs" / "rag_vectors" / "corpus.parquet"

_VECTOR_CACHE: List[Dict[str, object]] = []
_VECTOR_MTIME: float | None = None
_VECTOR_LOCK = threading.Lock()
_VECTOR_MISSING_WARNED = False
_FAISS_INDEX: "faiss.Index" | None = None  # type: ignore[name-defined]
_EMBEDDING_MATRIX: np.ndarray | None = None
_FAISS_UNAVAILABLE_WARNED = False
_REDIS_CACHE_KEY = "rag:vectors"
_RAG_STATUS: Dict[str, object] = {
    "available": False,
    "message": "RAG 向量尚未載入",
    "detail": None,
}


def get_status() -> Dict[str, object]:
    """Return a snapshot of the current RAG availability status."""

    with _VECTOR_LOCK:
        return dict(_RAG_STATUS)


def _update_status(*, available: bool, message: str, detail: str | None = None) -> None:
    _RAG_STATUS["available"] = available
    _RAG_STATUS["message"] = message
    _RAG_STATUS["detail"] = detail


def load_vectors(path: str | os.PathLike[str] = _DEFAULT_VECTOR_PATH) -> List[Dict[str, object]]:
    """Load vectors from a parquet file into memory."""
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(resolved_path)

    df = pd.read_parquet(resolved_path)
    required_columns = {"doc_path", "chunk_index", "text", "embedding"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in vector store: {missing}")

    vectors: List[Dict[str, object]] = []
    for row in df.itertuples(index=False):
        embedding_values = getattr(row, "embedding")
        vector = np.asarray(embedding_values, dtype=np.float32)
        meta = getattr(row, "meta", {})
        vectors.append(
            {
                "text": getattr(row, "text"),
                "embedding": vector,
                "doc": getattr(row, "doc_path"),
                "idx": int(getattr(row, "chunk_index")),
                "meta": meta if isinstance(meta, dict) else _safe_json(meta),
            }
        )
    return vectors


def ensure_vectors(path: str | os.PathLike[str] = _DEFAULT_VECTOR_PATH) -> List[Dict[str, object]]:
    """Ensure vectors are available, sharing cached state across workers via Redis when possible."""
    global _VECTOR_CACHE, _VECTOR_MTIME, _VECTOR_MISSING_WARNED
    resolved_path = Path(path)

    with _VECTOR_LOCK:
        redis_client = _get_redis_client()
        redis_payload = _load_cache_from_redis(redis_client) if redis_client else None

        file_exists = resolved_path.exists()
        file_mtime = resolved_path.stat().st_mtime if file_exists else None

        if file_exists and _VECTOR_CACHE and _VECTOR_MTIME == file_mtime:
            return _VECTOR_CACHE

        if redis_payload:
            cached_vectors, cached_matrix, cached_mtime = redis_payload
            if not file_exists or (
                file_mtime is not None
                and cached_mtime is not None
                and math.isclose(file_mtime, cached_mtime, rel_tol=0.0, abs_tol=1e-6)
            ):
                _VECTOR_CACHE = cached_vectors
                _VECTOR_MTIME = cached_mtime
                _VECTOR_MISSING_WARNED = False
                _rebuild_index(_VECTOR_CACHE, cached_matrix)
                _update_status(
                    available=bool(_VECTOR_CACHE),
                    message=(
                        f"RAG 向量已從 Redis 快取載入（{len(_VECTOR_CACHE)} 筆）"
                        if _VECTOR_CACHE
                        else "RAG 向量為空，功能將以降級模式執行"
                    ),
                    detail="redis-cache",
                )
                LOGGER.info("Loaded %s RAG chunks from Redis cache", len(_VECTOR_CACHE))
                return _VECTOR_CACHE

        if file_exists:
            _load_from_disk(resolved_path, redis_client, file_mtime)
            return _VECTOR_CACHE

        if not _VECTOR_MISSING_WARNED:
            _attempt_git_lfs_pull()
            if resolved_path.exists():
                file_mtime = resolved_path.stat().st_mtime
                _load_from_disk(resolved_path, redis_client, file_mtime)
            else:
                LOGGER.error(
                    "RAG 檔案遺失於 %s，RAG 功能將會被禁用", resolved_path
                )
                _update_status(
                    available=False,
                    message="RAG 檔案遺失，RAG 功能將會被禁用",
                    detail=str(resolved_path),
                )
                _VECTOR_MISSING_WARNED = True

        return _VECTOR_CACHE


def rag_query(
    query: str,
    top_k: int = 5,
    min_sim: float = 0.75,
    api_key: str | None = None,
) -> List[Dict[str, object]]:
    """Return the top matching chunks for the provided query string."""
    if not query:
        return []

    vectors = ensure_vectors()
    if not vectors:
        return []

    try:
        query_vector = embed_query(query, api_key=api_key)
    except EmbeddingError as exc:
        LOGGER.warning("Failed to embed query for RAG lookup: %s", exc)
        return []

    if not _FAISS_AVAILABLE:
        return _linear_search(query_vector, vectors, top_k=top_k, min_sim=min_sim)

    index = _FAISS_INDEX
    embeddings = _EMBEDDING_MATRIX
    if index is None or embeddings is None:
        return []

    query_vector = np.asarray(query_vector, dtype=np.float32)
    faiss.normalize_L2(query_vector.reshape(1, -1))

    search_k = min(len(vectors), top_k * 2)
    distances, indices = index.search(query_vector.reshape(1, -1), search_k)

    results: List[Dict[str, object]] = []
    for score, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        if score < min_sim:
            continue
        item = vectors[idx]
        results.append(
            {
                "text": item["text"],
                "doc": item["doc"],
                "idx": item["idx"],
                "score": float(score),
                "meta": item.get("meta", {}),
            }
        )
        if len(results) >= top_k:
            break

    return results


def _safe_json(value: object) -> Dict[str, object]:
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:  # pragma: no cover - best effort conversion
        return {"raw": value}


def _get_redis_client() -> object | None:
    if not has_app_context():
        return None
    try:
        return current_app.extensions.get("redis_client")
    except Exception:  # pragma: no cover - safety net for misconfigured app contexts
        return None


def _load_cache_from_redis(
    redis_client: object | None,
) -> Optional[Tuple[List[Dict[str, object]], np.ndarray, Optional[float]]]:
    if redis_client is None:
        return None

    try:
        raw = redis_client.get(_REDIS_CACHE_KEY)
    except Exception as exc:  # pragma: no cover - redis misconfiguration
        LOGGER.warning("Failed to fetch RAG cache from Redis: %s", exc)
        return None

    if not raw:
        return None

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    try:
        payload = json.loads(raw)
    except (TypeError, ValueError) as exc:
        LOGGER.warning("Invalid RAG cache payload in Redis: %s", exc)
        return None

    metadata = payload.get("metadata")
    embeddings_b64 = payload.get("embeddings")
    mtime_value = payload.get("mtime")
    if not metadata or embeddings_b64 is None:
        return None

    try:
        embeddings_bytes = base64.b64decode(embeddings_b64)
    except (ValueError, TypeError) as exc:
        LOGGER.warning("Failed to decode cached embeddings: %s", exc)
        return None

    try:
        matrix = np.load(io.BytesIO(embeddings_bytes), allow_pickle=False)
    except Exception as exc:  # pragma: no cover - corrupted cache
        LOGGER.warning("Failed to load cached embedding matrix: %s", exc)
        return None

    matrix = np.asarray(matrix, dtype=np.float32)
    if matrix.ndim == 1:
        if matrix.size == 0:
            matrix = matrix.reshape(0, 0)
        else:
            matrix = matrix.reshape(1, -1)

    if len(metadata) != len(matrix):
        LOGGER.warning(
            "Cached RAG payload mismatch: metadata=%s embeddings=%s", len(metadata), len(matrix)
        )
        return None

    vectors: List[Dict[str, object]] = []
    for meta_item, vector in zip(metadata, matrix):
        if not isinstance(meta_item, dict):
            LOGGER.warning("Skipping corrupted metadata item in RAG cache: %r", meta_item)
            continue

        text = meta_item.get("text", "")
        doc = meta_item.get("doc", "unknown")
        idx_value = meta_item.get("idx", 0)
        chunk_meta = meta_item.get("meta", {})

        if not isinstance(chunk_meta, dict):
            chunk_meta = _safe_json(chunk_meta)

        try:
            chunk_index = int(idx_value)
        except (TypeError, ValueError):
            chunk_index = 0

        vectors.append(
            {
                "text": text,
                "doc": doc,
                "idx": chunk_index,
                "meta": chunk_meta,
                "embedding": np.asarray(vector, dtype=np.float32),
            }
        )

    try:
        cached_mtime = float(mtime_value) if mtime_value is not None else None
    except (TypeError, ValueError):
        cached_mtime = None

    return vectors, matrix, cached_mtime


def _cache_in_redis(
    redis_client: object,
    vectors: List[Dict[str, object]],
    mtime: float | None,
    embeddings: np.ndarray | None,
) -> None:
    if redis_client is None:
        return

    try:
        # Persist the full snapshot without a TTL; mtime-based invalidation keeps the cache fresh.
        metadata = [
            {
                "text": item["text"],
                "doc": item["doc"],
                "idx": item["idx"],
                "meta": item.get("meta", {}),
            }
            for item in vectors
        ]

        if embeddings is None:
            if vectors:
                embeddings = np.vstack([item["embedding"] for item in vectors]).astype(np.float32)
            else:
                embeddings = np.empty((0, 0), dtype=np.float32)
        else:
            embeddings = np.asarray(embeddings, dtype=np.float32)

        buffer = io.BytesIO()
        np.save(buffer, embeddings, allow_pickle=False)
        payload = json.dumps(
            {
                "metadata": metadata,
                "embeddings": base64.b64encode(buffer.getvalue()).decode("ascii"),
                "mtime": mtime,
            },
            ensure_ascii=False,
        )

        redis_client.set(_REDIS_CACHE_KEY, payload)
    except Exception as exc:  # pragma: no cover - cache best effort
        LOGGER.warning("Failed to persist RAG cache to Redis: %s", exc)


def _attempt_git_lfs_pull() -> None:
    repo_root = _REPO_ROOT
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return

    try:
        commands = (["git", "lfs", "install", "--local"], ["git", "lfs", "pull"])
        for cmd_args in commands:
            result = subprocess.run(
                cmd_args,
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                LOGGER.warning(
                    "Command '%s' failed with code %s: %s",
                    " ".join(cmd_args),
                    result.returncode,
                    stderr,
                )
                break
    except FileNotFoundError:  # pragma: no cover - git not available in some envs
        LOGGER.warning("git or git-lfs not available; cannot pull RAG vectors")


def _load_from_disk(
    resolved_path: Path,
    redis_client: object | None,
    file_mtime: float | None,
) -> None:
    """Load vectors from disk and synchronise Redis cache."""
    global _VECTOR_CACHE, _VECTOR_MTIME, _VECTOR_MISSING_WARNED
    try:
        _VECTOR_CACHE = load_vectors(resolved_path)
        _rebuild_index(_VECTOR_CACHE)
        if file_mtime is None:
            file_mtime = resolved_path.stat().st_mtime
        _VECTOR_MTIME = file_mtime
        _VECTOR_MISSING_WARNED = False
        if redis_client is not None:
            _cache_in_redis(redis_client, _VECTOR_CACHE, file_mtime, _EMBEDDING_MATRIX)
        _update_status(
            available=bool(_VECTOR_CACHE),
            message=(
                f"RAG 向量載入完成（{len(_VECTOR_CACHE)} 筆）"
                if _VECTOR_CACHE
                else "RAG 向量為空，功能將以降級模式執行"
            ),
            detail=str(resolved_path),
        )
        LOGGER.info("Loaded %s RAG chunks from %s", len(_VECTOR_CACHE), resolved_path)
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.error("Failed to load RAG vectors from %s: %s", resolved_path, exc)
        _update_status(
            available=False,
            message="無法載入 RAG 檔案，RAG 功能將會被禁用",
            detail=str(exc),
        )
        _clear_cache(reset_status=False)


def _rebuild_index(vectors: List[Dict[str, object]], embeddings: Optional[np.ndarray] = None) -> None:
    """Build or refresh the FAISS index from in-memory vectors."""
    global _FAISS_INDEX, _EMBEDDING_MATRIX
    if not vectors:
        _FAISS_INDEX = None
        _EMBEDDING_MATRIX = None
        return

    if embeddings is None:
        embeddings = np.vstack([item["embedding"] for item in vectors]).astype(np.float32)
    else:
        embeddings = np.asarray(embeddings, dtype=np.float32)

    if _FAISS_AVAILABLE:
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        _FAISS_INDEX = index
    else:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        embeddings = embeddings / norms
        _FAISS_INDEX = None
    _EMBEDDING_MATRIX = embeddings


def _clear_cache(*, reset_status: bool = True) -> None:
    global _VECTOR_CACHE, _VECTOR_MTIME, _FAISS_INDEX, _EMBEDDING_MATRIX
    _VECTOR_CACHE = []
    _VECTOR_MTIME = None
    _FAISS_INDEX = None
    _EMBEDDING_MATRIX = None
    if reset_status:
        _update_status(available=False, message="RAG 向量尚未載入", detail=None)


def _linear_search(
    query_vector: np.ndarray,
    vectors: List[Dict[str, object]],
    *,
    top_k: int,
    min_sim: float,
) -> List[Dict[str, object]]:
    """Fallback cosine similarity search when FAISS is unavailable."""
    global _FAISS_UNAVAILABLE_WARNED
    if not _FAISS_UNAVAILABLE_WARNED:
        LOGGER.warning(
            "faiss-cpu not available; using linear scan fallback. Install the dependency for better RAG performance."
        )
        _FAISS_UNAVAILABLE_WARNED = True

    if not vectors:
        return []

    embeddings = _EMBEDDING_MATRIX
    if embeddings is None:
        embeddings = np.vstack([item["embedding"] for item in vectors]).astype(np.float32)
    query = np.asarray(query_vector, dtype=np.float32)
    norm = np.linalg.norm(query)
    if norm > 0:
        query = query / norm

    scores = embeddings @ query
    top_indices = np.argsort(scores)[::-1]

    results: List[Dict[str, object]] = []
    for idx in top_indices:
        score = float(scores[idx])
        if score < min_sim:
            continue
        item = vectors[int(idx)]
        results.append(
            {
                "text": item["text"],
                "doc": item["doc"],
                "idx": item["idx"],
                "score": score,
                "meta": item.get("meta", {}),
            }
        )
        if len(results) >= top_k:
            break

    return results
