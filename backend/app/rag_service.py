"""RAG 介面服務層，為本地向量庫與未來雲端提供統一介面。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Protocol

from .rag_loader import ensure_vectors, get_status, rag_query


LOGGER = logging.getLogger(__name__)


@dataclass
class RagChunk:
    text: str
    score: float
    source: str
    idx: int
    meta: dict[str, object]


class RagAdapter(Protocol):
    """RAG 搜尋後端介面。"""

    def warmup(self) -> None:
        ...

    def search(self, query: str, top_k: int, min_sim: float, api_key: str | None) -> Iterable[RagChunk]:
        ...

    def status(self) -> dict[str, object]:
        ...


class LocalFaissAdapter:
    """沿用既有本地 FAISS 資料結構的 Adapter。"""

    def warmup(self) -> None:
        ensure_vectors()

    def search(self, query: str, top_k: int, min_sim: float, api_key: str | None) -> Iterable[RagChunk]:
        chunks = rag_query(query, top_k=top_k, min_sim=min_sim, api_key=api_key)
        for chunk in chunks:
            yield RagChunk(
                text=str(chunk.get("text", "")),
                score=float(chunk.get("score", 0.0)),
                source=str(chunk.get("doc", "")),
                idx=int(chunk.get("idx", 0)),
                meta=dict(chunk.get("meta", {})),
            )

    def status(self) -> dict[str, object]:
        return get_status()


class RagService:
    """封裝 Adapter，統一提供 RAG 查詢介面。"""

    def __init__(self, adapter: RagAdapter | None = None):
        self.adapter: RagAdapter = adapter or LocalFaissAdapter()

    def ensure_ready(self) -> None:
        try:
            self.adapter.warmup()
        except Exception as exc:  # pragma: no cover - defensive: degrade gracefully when vectors missing
            LOGGER.warning("RAG warmup failed: %s", exc)

    def query(self, query: str, *, top_k: int = 5, min_sim: float = 0.75, api_key: str | None = None) -> list[RagChunk]:
        if not query:
            return []
        self.ensure_ready()
        return list(self.adapter.search(query, top_k=top_k, min_sim=min_sim, api_key=api_key))

    def status(self) -> dict[str, object]:
        self.ensure_ready()
        return self.adapter.status()


rag_service = RagService()

