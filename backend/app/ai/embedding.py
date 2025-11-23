"""Utilities for generating Gemini embeddings used by RAG flows."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIMENSION = 768
DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"
BATCH_SIZE = 32

_CLIENT_CACHE: dict[str, genai.Client] = {}
_CLIENT_LOCK = threading.Lock()


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails."""


@dataclass(frozen=True)
class _EmbeddingRequest:
    text: str
    task_type: str


def _resolve_api_key(explicit_key: str | None = None) -> str:
    api_key = explicit_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key == "your-gemini-api-key":
        raise EmbeddingError(
            "GOOGLE_API_KEY is not configured. Provide a valid key via the environment or request header."
        )
    return api_key


def _normalize_vector(values: Sequence[float]) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    return vector / norm


def _batch(items: list[_EmbeddingRequest], size: int) -> Iterable[list[_EmbeddingRequest]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _get_client(api_key: str) -> genai.Client:
    with _CLIENT_LOCK:
        client = _CLIENT_CACHE.get(api_key)
        if client is None:
            client = genai.Client(api_key=api_key)
            _CLIENT_CACHE[api_key] = client
        return client


def _perform_embedding_requests(requests_batch: List[_EmbeddingRequest], api_key: str) -> List[np.ndarray]:
    if not requests_batch:
        return []

    client = _get_client(api_key)
    contents = [item.text for item in requests_batch]
    task_type = requests_batch[0].task_type
    config = genai_types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=EMBEDDING_DIMENSION,
    )

    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=contents,
            config=config,
        )
    except genai_errors.APIError as exc:  # pragma: no cover - network failures handled here
        raise EmbeddingError(f"Embedding API error {exc.code}: {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive to wrap unexpected SDK issues
        raise EmbeddingError(f"Unexpected error while generating embeddings: {exc}") from exc

    embeddings = response.embeddings
    if not embeddings or len(embeddings) != len(requests_batch):
        raise EmbeddingError("Embedding response missing expected vectors.")

    vectors: List[np.ndarray] = []
    for embedding in embeddings:
        values = embedding.values if embedding else None
        if values is None:
            raise EmbeddingError("Embedding response contained an empty vector.")
        vectors.append(_normalize_vector(values))
    return vectors


def _embed(texts: Sequence[str], task_type: str, api_key: str | None = None) -> List[np.ndarray]:
    if not texts:
        return []

    resolved_key = _resolve_api_key(api_key)
    requests_list = [_EmbeddingRequest(text=text, task_type=task_type) for text in texts]

    vectors: List[np.ndarray] = []
    for batch_requests in _batch(requests_list, BATCH_SIZE):
        vectors.extend(_perform_embedding_requests(batch_requests, resolved_key))
    return vectors


def embed_documents(texts: Sequence[str], api_key: str | None = None) -> List[np.ndarray]:
    """Embed document chunks for retrieval."""
    return _embed(texts, DOCUMENT_TASK_TYPE, api_key)


def embed_query(text: str, api_key: str | None = None) -> np.ndarray:
    """Embed a single query string."""
    vectors = _embed([text], QUERY_TASK_TYPE, api_key)
    if not vectors:
        raise EmbeddingError("Embedding API returned no vector for the query.")
    return vectors[0]
