from time import perf_counter

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.rag.embeddings.base import BaseEmbeddingClient


logger = get_logger(__name__)


class LocalEmbeddingClient(BaseEmbeddingClient):
    """SentenceTransformers embedding client loaded on instance creation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        logger.info("Loading embedding model: %s", self.settings.EMBEDDING_MODEL_NAME)
        start_time = perf_counter()
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.settings.EMBEDDING_MODEL_NAME)
        except Exception:
            logger.exception(
                "Failed to load embedding model: %s",
                self.settings.EMBEDDING_MODEL_NAME,
            )
            raise
        logger.info("Embedding model loaded: elapsed=%.2fs", perf_counter() - start_time)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        start_time = perf_counter()
        logger.info("Embedding texts: count=%s", len(texts))
        if not texts:
            logger.info("Embedding texts skipped: count=0 elapsed=%.2fs", 0.0)
            return []
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        except Exception:
            logger.exception("Failed to encode texts: count=%s", len(texts))
            raise
        logger.info(
            "Embedding texts completed: count=%s elapsed=%.2fs",
            len(texts),
            perf_counter() - start_time,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        start_time = perf_counter()
        try:
            embedding = self.embed_texts([query])[0]
        except Exception:
            logger.exception("Failed to encode query")
            raise
        logger.info("Embedding query completed: elapsed=%.2fs", perf_counter() - start_time)
        return embedding
