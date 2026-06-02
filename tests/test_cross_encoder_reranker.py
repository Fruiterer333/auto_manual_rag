from app.data.schemas.models import Chunk, RetrievedChunk
from app.rag.rerankers.cross_encoder import CrossEncoderReranker, resolve_device


def _retrieved_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=chunk_id,
            doc_id=f"doc-{chunk_id}",
            source_file="manual.pdf",
            page=1,
            text=f"text-{chunk_id}",
            metadata={"existing": f"metadata-{chunk_id}"},
        ),
        score=score,
    )


class _FakeCrossEncoder:
    instances = []

    def __init__(self, model_name: str, **kwargs) -> None:
        self.model_name = model_name
        self.kwargs = kwargs
        self.predict_calls = []
        self.__class__.instances.append(self)

    def predict(self, pairs, **kwargs):
        self.predict_calls.append((pairs, kwargs))
        return [0.1, 0.9, 0.3]


def test_cross_encoder_reranker_sorts_scores_and_preserves_chunk_values(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.rag.rerankers.cross_encoder._load_cross_encoder_class",
        lambda: _FakeCrossEncoder,
    )
    reranker = CrossEncoderReranker(
        model_name="test-reranker",
        device="cpu",
        batch_size=4,
        max_length=128,
    )
    chunks = [
        _retrieved_chunk("chunk-a", 0.7),
        _retrieved_chunk("chunk-b", 0.6),
        _retrieved_chunk("chunk-c", 0.5),
    ]

    result = reranker.rerank("question", chunks, top_k=2)

    assert [item.chunk.chunk_id for item in result] == ["chunk-b", "chunk-c"]
    assert [item.score for item in result] == [0.6, 0.5]
    assert [item.chunk.text for item in result] == ["text-chunk-b", "text-chunk-c"]
    assert result[0].chunk.metadata == {
        "existing": "metadata-chunk-b",
        "rerank_score": 0.9,
        "original_rank": 2,
        "rerank_model_name": "test-reranker",
        "rerank_applied": True,
        "rerank_elapsed_ms": result[0].chunk.metadata["rerank_elapsed_ms"],
        "rerank_rank": 1,
    }
    assert result[1].chunk.metadata["rerank_score"] == 0.3
    assert result[1].chunk.metadata["original_rank"] == 3
    assert result[1].chunk.metadata["rerank_rank"] == 2
    assert _FakeCrossEncoder.instances[-1].kwargs == {
        "device": "cpu",
        "max_length": 128,
    }
    assert _FakeCrossEncoder.instances[-1].predict_calls == [
        (
            [
                ("question", "text-chunk-a"),
                ("question", "text-chunk-b"),
                ("question", "text-chunk-c"),
            ],
            {"batch_size": 4, "show_progress_bar": False},
        )
    ]


def test_cross_encoder_reranker_returns_empty_chunks_without_predict(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.rag.rerankers.cross_encoder._load_cross_encoder_class",
        lambda: _FakeCrossEncoder,
    )
    reranker = CrossEncoderReranker(model_name="test-reranker", device="cpu")

    assert reranker.rerank("question", []) == []
    assert _FakeCrossEncoder.instances[-1].predict_calls == []


def test_resolve_device_accepts_cpu_without_hardware_detection() -> None:
    assert resolve_device("cpu") == "cpu"

