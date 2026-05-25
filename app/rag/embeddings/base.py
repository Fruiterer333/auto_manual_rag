from abc import ABC, abstractmethod


class BaseEmbeddingClient(ABC):
    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of texts."""

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Return embedding for one query."""
