import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.rag.chains.qa_chain import QAChain
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.retrievers.context_selector import (
    enforce_max_context_chars,
    expand_neighbor_contexts,
    select_contexts,
)
from app.rag.retrievers.chunk_filters import (
    deduplicate_chunks_by_content,
    filter_retrieval_chunks,
)
from app.rag.retrievers.hybrid_retriever import HybridRetriever
from app.rag.utils.citation_utils import build_relevant_quote


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a question against the manual index.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--debug-retrieval", action="store_true")
    parser.add_argument("--show-full-chunk", action="store_true")
    parser.add_argument("--use-context-selection", action="store_true")
    parser.add_argument("--retrieval-mode", choices=["dense", "bm25", "hybrid"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.debug_retrieval:
        debug_retrieval(
            question=args.question,
            top_k=args.top_k,
            show_full_chunk=args.show_full_chunk,
            use_context_selection=args.use_context_selection,
            retrieval_mode=args.retrieval_mode,
        )
        return

    response = QAChain().answer(
        question=args.question,
        top_k=args.top_k,
        retrieval_mode=args.retrieval_mode,
    )

    print(f"问题：{response.question}")
    print(f"回答：{response.answer}")
    print("引用：")
    for citation in response.citations:
        score = citation.score if citation.score is not None else "N/A"
        distance = citation.distance if citation.distance is not None else "N/A"
        print(
            f"- score={score} distance={distance} "
            f"page={citation.page} chunk_id={citation.chunk_id}"
        )
        print(f"  quote={citation.quote}")


def debug_retrieval(
    question: str,
    top_k: int,
    show_full_chunk: bool = False,
    use_context_selection: bool = False,
    retrieval_mode: str | None = None,
) -> None:
    settings = get_settings()
    embedding_client = LocalEmbeddingClient(settings)
    retriever = HybridRetriever(settings)
    mode = retrieval_mode or settings.RETRIEVAL_MODE
    query_embedding = embedding_client.embed_query(question)
    candidate_k = top_k
    if use_context_selection:
        candidate_k = max(top_k, settings.CONTEXT_SELECTION_CANDIDATE_K)
    results = retriever.search(
        question=question,
        query_embedding=query_embedding,
        top_k=candidate_k,
        candidate_k=candidate_k,
        retrieval_mode=mode,
    )
    debug_info = retriever.last_debug_info
    duplicate_removed_count = 0
    if use_context_selection:
        before_selection_count = len(results)
        results, selection_filter_summary = filter_retrieval_chunks(
            results,
            stage="context_selection_pre",
        )
        results, selection_pre_dedup_summary = deduplicate_chunks_by_content(
            results,
            stage="context_selection_pre",
        )
        results = select_contexts(
            question=question,
            retrieved=results,
            top_k=top_k,
            enabled=True,
        )
        results, selection_post_dedup_summary = deduplicate_chunks_by_content(
            results,
            stage="context_selection_post",
        )
        duplicate_removed_count += selection_pre_dedup_summary["duplicate_removed_count"]
        duplicate_removed_count += selection_post_dedup_summary["duplicate_removed_count"]
        expanded_count = 0
        expansion_dedup_summary = {}
        if settings.ENABLE_NEIGHBOR_CONTEXT_EXPANSION:
            before_expansion_count = len(results)
            results = expand_neighbor_contexts(
                results,
                neighbor_lookup=retriever.find_neighbor_chunks,
                enabled=True,
                max_per_chunk=settings.NEIGHBOR_EXPANSION_MAX_PER_CHUNK,
            )
            expanded_count = len(results) - before_expansion_count
            results, expansion_dedup_summary = deduplicate_chunks_by_content(
                results,
                stage="neighbor_expansion_post",
            )
            duplicate_removed_count += expansion_dedup_summary["duplicate_removed_count"]
        results, final_filter_summary = filter_retrieval_chunks(
            results,
            stage="final_context_pre_prompt",
        )
        results, final_dedup_summary = deduplicate_chunks_by_content(
            results,
            stage="final_context_pre_prompt",
        )
        duplicate_removed_count += final_dedup_summary["duplicate_removed_count"]
        results = enforce_max_context_chars(results, settings.MAX_CONTEXT_CHARS)
    else:
        expanded_count = 0
        before_selection_count = len(results)
        selection_filter_summary = {}
        selection_pre_dedup_summary = {}
        selection_post_dedup_summary = {}
        expansion_dedup_summary = {}
        final_filter_summary = {}
        final_dedup_summary = {}

    print(f"问题：{question}")
    view_mode = "metadata-aware selection" if use_context_selection else "raw retrieval"
    print(f"检索结果：{view_mode}")
    print(f"retrieval_mode={mode}")
    print(f"bm25_query_tokens_raw={debug_info.get('bm25_query_tokens_raw', [])}")
    print(f"bm25_query_tokens_filtered={debug_info.get('bm25_query_tokens_filtered', [])}")
    print(f"bm25_query_filtered_terms={debug_info.get('bm25_query_filtered_terms', [])}")
    print(f"bm25_core_terms={debug_info.get('bm25_core_terms', [])}")
    print(f"bm25_coverage_terms={debug_info.get('bm25_coverage_terms', [])}")
    print(f"dense_filter_summary={debug_info.get('dense_filter_summary', {})}")
    print(f"bm25_filter_summary={debug_info.get('bm25_filter_summary', {})}")
    print(f"fused_filter_summary={debug_info.get('fused_filter_summary', {})}")
    print(f"fused_dedup_summary={debug_info.get('fused_dedup_summary', {})}")
    fused_filter_summary = debug_info.get("fused_filter_summary", {})
    print(f"before_filter_count={fused_filter_summary.get('before_filter_count', 'N/A')}")
    print(f"after_filter_count={fused_filter_summary.get('after_filter_count', 'N/A')}")
    print(f"removed_toc_count={fused_filter_summary.get('removed_toc_count', 'N/A')}")
    print(f"removed_noise_count={fused_filter_summary.get('removed_noise_count', 'N/A')}")
    print(
        "removed_reasons="
        f"{fused_filter_summary.get('filter_reason_counts', {})}"
    )
    if use_context_selection:
        print(
            "summary="
            f"before_selection_count={before_selection_count}, "
            f"selection_filter_summary={selection_filter_summary}, "
            f"selection_pre_dedup_summary={selection_pre_dedup_summary}, "
            f"selection_post_dedup_summary={selection_post_dedup_summary}, "
            f"duplicate_removed_count={duplicate_removed_count}, "
            f"expansion_enabled={settings.ENABLE_NEIGHBOR_CONTEXT_EXPANSION}, "
            f"expanded_count={expanded_count}, "
            f"expansion_dedup_summary={expansion_dedup_summary}, "
            f"final_filter_summary={final_filter_summary}, "
            f"final_dedup_summary={final_dedup_summary}, "
            f"final_context_count={len(results)}"
        )
    for rank, result in enumerate(results, start=1):
        chunk = result.chunk
        score = result.score if result.score is not None else "N/A"
        distance = result.distance if result.distance is not None else "N/A"
        chunk_text = chunk.text if show_full_chunk else chunk.text[:300].replace("\n", " ")
        quote = build_relevant_quote(question, chunk.text)
        print(f"\nrank={rank}")
        print(f"final_context_rank={rank}")
        print(f"score={score}")
        print(f"selection_score={result.selection_score if result.selection_score is not None else 'N/A'}")
        print(f"distance={distance}")
        if settings.ENABLE_NEIGHBOR_CONTEXT_EXPANSION:
            print(f"is_expanded_neighbor={str(result.is_expanded_neighbor).lower()}")
        print(f"retrieval_source={chunk.metadata.get('retrieval_source', 'N/A')}")
        print(f"dense_rank={chunk.metadata.get('dense_rank', 'N/A')}")
        print(f"bm25_rank={chunk.metadata.get('bm25_rank', 'N/A')}")
        print(f"dense_score={chunk.metadata.get('dense_score', 'N/A')}")
        print(f"bm25_score={chunk.metadata.get('bm25_score', 'N/A')}")
        print(f"rrf_score={chunk.metadata.get('rrf_score', 'N/A')}")
        print(f"is_toc={chunk.metadata.get('is_toc', False)}")
        print(f"is_noise={chunk.metadata.get('is_noise', False)}")
        print(f"filter_reason={chunk.metadata.get('filter_reason', 'N/A')}")
        print(f"bm25_penalty_applied={chunk.metadata.get('bm25_penalty_applied', 'N/A')}")
        print(f"bm25_penalty_reason={chunk.metadata.get('bm25_penalty_reason', 'N/A')}")
        print(f"bm25_coverage_terms={chunk.metadata.get('bm25_coverage_terms', 'N/A')}")
        print(
            "bm25_coverage_matched_terms="
            f"{chunk.metadata.get('bm25_coverage_matched_terms', 'N/A')}"
        )
        print(
            "bm25_coverage_missing_terms="
            f"{chunk.metadata.get('bm25_coverage_missing_terms', 'N/A')}"
        )
        print(
            "bm25_score_before_penalty="
            f"{chunk.metadata.get('bm25_score_before_penalty', 'N/A')}"
        )
        print(
            "bm25_score_after_penalty="
            f"{chunk.metadata.get('bm25_score_after_penalty', 'N/A')}"
        )
        print(f"page={chunk.page}")
        print(f"chunk_id={chunk.chunk_id}")
        print(f"source_file={chunk.source_file}")
        print(f"chapter={chunk.chapter or 'N/A'}")
        print(f"section={chunk.section or 'N/A'}")
        print(f"content_type={chunk.content_type or 'N/A'}")
        print(f"risk_level={chunk.risk_level or 'N/A'}")
        label = "full_chunk" if show_full_chunk else "text_preview"
        print(f"{label}={chunk_text}")
        print(f"relevant_quote={quote}")


if __name__ == "__main__":
    main()
