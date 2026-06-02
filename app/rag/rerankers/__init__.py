from app.core.config import Settings
from app.core.logger import get_logger
from app.rag.rerankers.base import BaseReranker
from app.rag.rerankers.cross_encoder import CrossEncoderReranker
from app.rag.rerankers.noop import NoopReranker


logger = get_logger(__name__)


def get_reranker(settings: Settings) -> BaseReranker:
    """Return the configured reranker implementation.

    The model is only loaded when rerank is explicitly enabled.
    """
    if settings.ENABLE_RERANK:
        return CrossEncoderReranker(
            model_name=settings.RERANK_MODEL_NAME,
            device=settings.RERANK_DEVICE,
            batch_size=settings.RERANK_BATCH_SIZE,
            max_length=settings.RERANK_MAX_LENGTH,
        )
    return NoopReranker()


__all__ = ["BaseReranker", "CrossEncoderReranker", "NoopReranker", "get_reranker"]
