from app.core.config import Settings
from app.data.schemas.models import Chunk, RetrievedChunk
from app.rag.rerankers import get_reranker
from app.rag.rerankers.noop import NoopReranker
from app.rag.chains.qa_chain import QAChain


def _retrieved_chunk(
    chunk_id: str,
    score: float,
    *,
    text: str | None = None,
    content_type: str | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=chunk_id,
            doc_id=f"doc-{chunk_id}",
            source_file="manual.pdf",
            page=1,
            text=text or f"text-{chunk_id}",
            content_type=content_type,
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


def test_reranker_factory_returns_noop_when_disabled(monkeypatch) -> None:
    def fail_if_constructed(**kwargs):
        raise AssertionError(f"CrossEncoderReranker should not be constructed: {kwargs}")

    monkeypatch.setattr("app.rag.rerankers.CrossEncoderReranker", fail_if_constructed)
    settings = Settings(ENABLE_RERANK=False)

    assert isinstance(get_reranker(settings), NoopReranker)


def test_reranker_factory_constructs_cross_encoder_when_enabled(monkeypatch) -> None:
    calls = []

    class FakeCrossEncoderReranker:
        def __init__(self, **kwargs) -> None:
            calls.append(kwargs)

    monkeypatch.setattr("app.rag.rerankers.CrossEncoderReranker", FakeCrossEncoderReranker)
    settings = Settings(ENABLE_RERANK=True)

    result = get_reranker(settings)

    assert isinstance(result, FakeCrossEncoderReranker)
    assert calls == [
        {
            "model_name": "BAAI/bge-reranker-base",
            "device": "auto",
            "batch_size": 8,
            "max_length": 512,
        }
    ]


class _FakeEmbeddingClient:
    def embed_query(self, text: str) -> list[float]:
        assert text == "如何执行操作？"
        return [0.1, 0.2]


class _FakeRetriever:
    def __init__(self, chunks: list[RetrievedChunk], expected_candidate_k: int = 2) -> None:
        self.chunks = chunks
        self.expected_candidate_k = expected_candidate_k

    def search(self, **kwargs) -> list[RetrievedChunk]:
        assert kwargs["top_k"] == self.expected_candidate_k
        assert kwargs["candidate_k"] == self.expected_candidate_k
        return self.chunks


class _FakeLLMClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        assert "如何执行操作？" in prompt
        self.prompts.append(prompt)
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


class _RecordingReverseReranker(NoopReranker):
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str], int | None]] = []

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        self.calls.append((query, [item.chunk.chunk_id for item in chunks], top_k))
        reranked = list(reversed(chunks))
        return reranked if top_k is None else reranked[:top_k]


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


def test_qa_chain_rerank_hook_limits_candidates_when_enabled() -> None:
    chunks = [
        _retrieved_chunk("chunk-1", 0.9),
        _retrieved_chunk("chunk-2", 0.8),
        _retrieved_chunk("chunk-3", 0.7),
    ]
    reranker = _RecordingReverseReranker()
    chain = QAChain(
        settings=Settings(
            ENABLE_RERANK=True,
            RERANK_TOP_N=3,
            RERANK_OUTPUT_TOP_K=2,
            ENABLE_METADATA_CONTEXT_SELECTION=False,
            ENABLE_NEIGHBOR_CONTEXT_EXPANSION=False,
        ),
        embedding_client=_FakeEmbeddingClient(),
        retriever=_FakeRetriever(chunks, expected_candidate_k=3),
        llm_client=_FakeLLMClient(),
        reranker=reranker,
    )

    response = chain.answer("如何执行操作？", top_k=2, retrieval_mode="hybrid")

    assert reranker.calls == [("如何执行操作？", ["chunk-1", "chunk-2", "chunk-3"], 2)]
    assert [citation.chunk_id for citation in response.citations] == ["chunk-3", "chunk-2"]


def test_answer_postprocess_removes_explicit_evidence_reference_only() -> None:
    chain = QAChain.__new__(QAChain)

    assert chain._post_process_answer("根据 Evidence E1，执行该操作。") == "执行该操作。"
    assert chain._post_process_answer("车辆显示故障代码 E1") == "车辆显示故障代码 E1"


class _NeighborFakeRetriever(_FakeRetriever):
    def __init__(
        self,
        chunks: list[RetrievedChunk],
        neighbors: dict[str, list[RetrievedChunk]],
    ) -> None:
        super().__init__(chunks, expected_candidate_k=len(chunks))
        self.neighbors = neighbors

    def find_neighbor_chunks(self, chunk: Chunk, max_per_chunk: int) -> list[RetrievedChunk]:
        return self.neighbors.get(chunk.chunk_id, [])[:max_per_chunk]


def test_qa_chain_uses_same_count_limited_contexts_for_prompt_and_citations() -> None:
    chunks = [
        _retrieved_chunk(
            f"chunk-{index}",
            1.0 - index / 10,
            text=f"第{index}条原始证据内容。",
            content_type="procedure",
        )
        for index in range(1, 6)
    ]
    neighbors = {
        item.chunk.chunk_id: [
            _retrieved_chunk(
                f"neighbor-{index}",
                0.1,
                text=f"第{index}条扩展证据内容。",
            )
        ]
        for index, item in enumerate(chunks, start=1)
    }
    llm_client = _FakeLLMClient()
    chain = QAChain(
        settings=Settings(
            ENABLE_RERANK=False,
            ENABLE_METADATA_CONTEXT_SELECTION=False,
            ENABLE_NEIGHBOR_CONTEXT_EXPANSION=True,
            NEIGHBOR_EXPANSION_MAX_PER_CHUNK=1,
            MAX_CONTEXT_CHARS=6000,
        ),
        embedding_client=_FakeEmbeddingClient(),
        retriever=_NeighborFakeRetriever(chunks, neighbors),
        llm_client=llm_client,
        reranker=NoopReranker(),
    )

    response = chain.answer("如何执行操作？", top_k=5, retrieval_mode="hybrid")
    prompt = llm_client.prompts[0]
    citation_ids = [citation.chunk_id for citation in response.citations]

    assert citation_ids == [f"chunk-{index}" for index in range(1, 6)]
    assert len(citation_ids) == 5
    assert prompt.count("[EVIDENCE E") == 5
    for index in range(1, 6):
        assert f"第{index}条原始证据内容。" in prompt
        assert f"第{index}条扩展证据内容。" not in prompt


def test_qa_chain_excludes_char_budgeted_contexts_from_prompt_and_citations() -> None:
    chunks = [
        _retrieved_chunk("chunk-1", 0.9, text="第一证据。"),
        _retrieved_chunk("chunk-2", 0.8, text="第二条证据超过剩余字符预算。"),
        _retrieved_chunk("chunk-3", 0.7, text="第三证据。"),
    ]
    llm_client = _FakeLLMClient()
    chain = QAChain(
        settings=Settings(
            ENABLE_RERANK=False,
            ENABLE_METADATA_CONTEXT_SELECTION=False,
            ENABLE_NEIGHBOR_CONTEXT_EXPANSION=False,
            MAX_CONTEXT_CHARS=8,
        ),
        embedding_client=_FakeEmbeddingClient(),
        retriever=_FakeRetriever(chunks, expected_candidate_k=3),
        llm_client=llm_client,
        reranker=NoopReranker(),
    )

    response = chain.answer("如何执行操作？", top_k=3, retrieval_mode="hybrid")
    prompt = llm_client.prompts[0]

    assert [citation.chunk_id for citation in response.citations] == ["chunk-1"]
    assert "第一证据。" in prompt
    assert "第二条证据超过剩余字符预算。" not in prompt
    assert "第三证据。" not in prompt
