from app.core.config import Settings
from app.core.logger import get_logger
from app.rag.rerankers.base import BaseReranker
from app.rag.rerankers.noop import NoopReranker


logger = get_logger(__name__)


def get_reranker(settings: Settings) -> BaseReranker:
    """Return the configured reranker implementation.

    V3.1.0 only provides the compatibility implementation. A real local
    cross-encoder can be added behind this factory in V3.1.1.
    """
    if settings.ENABLE_RERANK:
        logger.warning(
            "Rerank enabled but real reranker is not implemented yet; using NoopReranker"
        )
    return NoopReranker()


__all__ = ["BaseReranker", "NoopReranker", "get_reranker"]

