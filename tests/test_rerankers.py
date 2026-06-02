from app.core.config import Settings
from app.data.schemas.models import Chunk, RetrievedChunk
from app.rag.rerankers import get_reranker
from app.rag.rerankers.noop import NoopReranker
from app.rag.chains.qa_chain import QAChain


def _retrieved_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=chunk_id,
            doc_id=f"doc-{chunk_id}",
            source_file="manual.pdf",
            page=1,
            text=f"text-{chunk_id}",
            metadata={"section": f"section-{chunk_id}"},
        ),
        score=score,
    )


def test_noop_reranker_preserves_full_input_order_and_values() -> None:
    chunks = [
        _retrieved_chunk("chunk-1", 0.9),
        _retrieved_chunk("chunk-2", 0.8),
        _retrieved_chunk("chunk-3", 0.7),
    ]

    result = NoopReranker().rerank("question", chunks)

    assert result is not chunks
    assert [item.chunk.chunk_id for item in result] == [
        "chunk-1",
        "chunk-2",
        "chunk-3",
    ]
    assert [item.score for item in result] == [0.9, 0.8, 0.7]
    assert [item.chunk.text for item in result] == [
        "text-chunk-1",
        "text-chunk-2",
        "text-chunk-3",
    ]
    assert [item.chunk.metadata for item in result] == [
        {"section": "section-chunk-1"},
        {"section": "section-chunk-2"},
        {"section": "section-chunk-3"},
    ]


def test_noop_reranker_limits_output_without_reordering() -> None:
    chunks = [
        _retrieved_chunk("chunk-1", 0.9),
        _retrieved_chunk("chunk-2", 0.8),
        _retrieved_chunk("chunk-3", 0.7),
    ]

    result = NoopReranker().rerank("question", chunks, top_k=2)

    assert [item.chunk.chunk_id for item in result] == ["chunk-1", "chunk-2"]


def test_reranker_factory_returns_noop_when_disabled() -> None:
    settings = Settings(ENABLE_RERANK=False)

    assert isinstance(get_reranker(settings), NoopReranker)


def test_reranker_factory_falls_back_to_noop_when_enabled() -> None:
    settings = Settings(ENABLE_RERANK=True)

    assert isinstance(get_reranker(settings), NoopReranker)


class _FakeEmbeddingClient:
    def embed_query(self, text: str) -> list[float]:
        assert text == "如何执行操作？"
        return [0.1, 0.2]


class _FakeRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks

    def search(self, **kwargs) -> list[RetrievedChunk]:
        assert kwargs["top_k"] == 2
        assert kwargs["candidate_k"] == 2
        return self.chunks


class _FakeLLMClient:
    def generate(self, prompt: str) -> str:
        assert "如何执行操作？" in prompt
        return "按照手册执行操作。"


class _RecordingNoopReranker(NoopReranker):
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str], int | None]] = []

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        self.calls.append((query, [item.chunk.chunk_id for item in chunks], top_k))
        return super().rerank(query, chunks, top_k)


def test_qa_chain_noop_hook_preserves_default_candidate_order() -> None:
    chunks = [
        _retrieved_chunk("chunk-1", 0.9),
        _retrieved_chunk("chunk-2", 0.8),
    ]
    reranker = _RecordingNoopReranker()
    chain = QAChain(
        settings=Settings(
            ENABLE_RERANK=False,
            ENABLE_METADATA_CONTEXT_SELECTION=False,
            ENABLE_NEIGHBOR_CONTEXT_EXPANSION=False,
        ),
        embedding_client=_FakeEmbeddingClient(),
        retriever=_FakeRetriever(chunks),
        llm_client=_FakeLLMClient(),
        reranker=reranker,
    )

    response = chain.answer("如何执行操作？", top_k=2, retrieval_mode="hybrid")

    assert reranker.calls == [("如何执行操作？", ["chunk-1", "chunk-2"], None)]
    assert [citation.chunk_id for citation in response.citations] == ["chunk-1", "chunk-2"]
