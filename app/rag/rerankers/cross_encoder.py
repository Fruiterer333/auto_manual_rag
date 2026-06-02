from time import perf_counter
from typing import Any

from app.core.logger import get_logger
from app.data.schemas.models import RetrievedChunk
from app.rag.rerankers.base import BaseReranker


logger = get_logger(__name__)


class CrossEncoderReranker(BaseReranker):
    """Local sentence-transformers cross-encoder reranker."""

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        batch_size: int = 8,
        max_length: int = 512,
    ) -> None:
        self.model_name = model_name
        self.device = resolve_device(device)
        self.batch_size = batch_size
        self.max_length = max_length
        logger.info(
            "Loading cross-encoder reranker: model=%s device=%s max_length=%s",
            self.model_name,
            self.device,
            self.max_length,
        )
        start_time = perf_counter()
        try:
            cross_encoder_class = _load_cross_encoder_class()
            self.model = cross_encoder_class(
                self.model_name,
                device=self.device,
                max_length=self.max_length,
            )
        except ImportError:
            logger.exception("sentence-transformers is required when rerank is enabled")
            raise
        except Exception as exc:
            logger.exception("Failed to load cross-encoder reranker: model=%s", self.model_name)
            raise RuntimeError(
                f"Failed to load cross-encoder reranker model: {self.model_name}"
            ) from exc
        logger.info(
            "Cross-encoder reranker loaded: model=%s device=%s elapsed=%.2fs",
            self.model_name,
            self.device,
            perf_counter() - start_time,
        )

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        start_time = perf_counter()
        pairs = [(query, item.chunk.text) for item in chunks]
        try:
            raw_scores = self.model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )
            scores = _to_float_scores(raw_scores)
        except Exception:
            logger.exception("Failed to rerank chunks: model=%s count=%s", self.model_name, len(chunks))
            raise
        if len(scores) != len(chunks):
            raise ValueError(
                f"Cross-encoder returned {len(scores)} scores for {len(chunks)} chunks"
            )

        elapsed_ms = (perf_counter() - start_time) * 1000
        scored_chunks: list[RetrievedChunk] = []
        for original_rank, (item, score) in enumerate(zip(chunks, scores), start=1):
            metadata = {
                **item.chunk.metadata,
                "rerank_score": score,
                "original_rank": original_rank,
                "rerank_model_name": self.model_name,
                "rerank_applied": True,
                "rerank_elapsed_ms": elapsed_ms,
            }
            scored_chunks.append(
                item.model_copy(
                    update={
                        "chunk": item.chunk.model_copy(update={"metadata": metadata}),
                    }
                )
            )

        sorted_chunks = sorted(
            scored_chunks,
            key=lambda item: float(item.chunk.metadata["rerank_score"]),
            reverse=True,
        )
        reranked_chunks = [
            item.model_copy(
                update={
                    "chunk": item.chunk.model_copy(
                        update={
                            "metadata": {
                                **item.chunk.metadata,
                                "rerank_rank": rerank_rank,
                            }
                        }
                    )
                }
            )
            for rerank_rank, item in enumerate(sorted_chunks, start=1)
        ]
        logger.info(
            "Cross-encoder rerank completed: model=%s candidates=%s returned=%s elapsed_ms=%.2f",
            self.model_name,
            len(chunks),
            len(reranked_chunks) if top_k is None else min(top_k, len(reranked_chunks)),
            elapsed_ms,
        )
        return reranked_chunks if top_k is None else reranked_chunks[:top_k]


def resolve_device(device: str) -> str:
    requested = device.lower()
    if requested not in {"auto", "cpu", "mps", "cuda"}:
        raise ValueError(f"Unsupported rerank device: {device}")
    if requested == "cpu":
        return "cpu"

    try:
        import torch
    except ImportError:
        logger.warning("torch is unavailable; falling back to CPU for rerank")
        return "cpu"

    cuda_available = bool(torch.cuda.is_available())
    mps_available = bool(
        hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    )
    if requested == "cuda":
        if cuda_available:
            return "cuda"
        logger.warning("CUDA is unavailable; falling back to CPU for rerank")
        return "cpu"
    if requested == "mps":
        if mps_available:
            return "mps"
        logger.warning("MPS is unavailable; falling back to CPU for rerank")
        return "cpu"
    if cuda_available:
        return "cuda"
    if mps_available:
        return "mps"
    return "cpu"


def _load_cross_encoder_class():
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers is required when ENABLE_RERANK=true. "
            "Install it with: pip install sentence-transformers"
        ) from exc
    return CrossEncoder


def _to_float_scores(raw_scores: Any) -> list[float]:
    values = raw_scores.tolist() if hasattr(raw_scores, "tolist") else list(raw_scores)
    scores: list[float] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            if len(value) != 1:
                raise ValueError("Cross-encoder must return one relevance score per chunk")
            value = value[0]
        scores.append(float(value))
    return scores

