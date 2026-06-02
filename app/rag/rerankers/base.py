from abc import ABC, abstractmethod

from app.data.schemas.models import RetrievedChunk


class BaseReranker(ABC):
    """Interface for optional query-chunk reranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Return chunks in reranked order, optionally limited to top_k."""

