import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.data.schemas.models import Chunk
from app.rag.retrievers.bm25_retriever import BM25Retriever
from app.rag.retrievers.chunk_filters import inspect_chunk_filter
from app.rag.retrievers.tokenizer import tokenize_query_for_bm25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect indexed manual chunks.")
    parser.add_argument("--page", type=int)
    parser.add_argument("--page-range", nargs=2, type=int, metavar=("START", "END"))
    parser.add_argument("--section")
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--show-full", action="store_true")
    parser.add_argument("--show-filtered", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    retriever = BM25Retriever(get_settings())
    retriever.load_index()
    chunks = list(retriever.chunks)
    if args.show_filtered:
        chunks.extend(retriever.filtered_chunks)
    print(
        "source=bm25_index "
        f"indexed_chunks={len(retriever.chunks)} "
        f"filtered_chunks={len(retriever.filtered_chunks)} "
        f"show_filtered={args.show_filtered}"
    )

    if args.page is not None:
        chunks = [chunk for chunk in chunks if chunk.page == args.page]
    if args.page_range:
        start, end = args.page_range
        chunks = [
            chunk for chunk in chunks
            if chunk.page is not None and start <= chunk.page <= end
        ]
    if args.section:
        chunks = [
            chunk for chunk in chunks
            if args.section in (chunk.section or "")
        ]
    if args.query:
        chunks = _rank_by_query(chunks, args.query)
    else:
        chunks = sorted(chunks, key=_chunk_order_key)
    if not args.show_filtered:
        chunks = [
            chunk for chunk in chunks
            if not _is_filtered_for_inspection(chunk)
        ]

    for index, chunk in enumerate(chunks[: args.limit], start=1):
        _print_chunk(index, chunk, show_full=args.show_full)


def _rank_by_query(chunks: list[Chunk], query: str) -> list[Chunk]:
    tokens = tokenize_query_for_bm25(query)

    def score(chunk: Chunk) -> tuple[int, int]:
        text = chunk.text
        hits = sum(1 for token in tokens if token and token in text)
        return hits, -_chunk_order_key(chunk)[0]

    return sorted(
        [chunk for chunk in chunks if score(chunk)[0] > 0],
        key=score,
        reverse=True,
    )


def _print_chunk(index: int, chunk: Chunk, show_full: bool) -> None:
    filter_info = inspect_chunk_filter(chunk, stage="inspect_chunks")
    text = chunk.text if show_full else chunk.text[:300].replace("\n", " ")
    print(f"\nindex={index}")
    print("source=bm25_index")
    print(f"stage={filter_info['stage']}")
    print(f"index_status={chunk.metadata.get('index_status', 'indexed')}")
    print(f"chunk_id={chunk.chunk_id}")
    print(f"chunk_index={chunk.metadata.get('chunk_index', 'N/A')}")
    print(f"page={chunk.page}")
    print(f"chapter={chunk.chapter or 'N/A'}")
    print(f"section={chunk.section or 'N/A'}")
    print(f"subsection={chunk.subsection or chunk.metadata.get('subsection') or 'N/A'}")
    print(f"content_type={chunk.content_type or 'N/A'}")
    print(f"risk_level={chunk.risk_level or 'N/A'}")
    print(f"source_file={chunk.source_file}")
    print(f"text_length={len(chunk.text)}")
    print(f"is_toc={filter_info['is_toc']}")
    print(f"is_noise={filter_info['is_noise']}")
    print(f"filter_reason={filter_info['filter_reason'] or 'N/A'}")
    label = "full_text" if show_full else "text_preview"
    print(f"{label}={text}")


def _chunk_order_key(chunk: Chunk) -> tuple[int, int]:
    page = chunk.page if chunk.page is not None else 999999
    chunk_index = chunk.metadata.get("chunk_index")
    if isinstance(chunk_index, int):
        index = chunk_index
    elif isinstance(chunk_index, str) and chunk_index.isdigit():
        index = int(chunk_index)
    else:
        index = 999999
    return page, index


def _is_filtered_for_inspection(chunk: Chunk) -> bool:
    filter_info = inspect_chunk_filter(chunk, stage="inspect_chunks")
    return bool(filter_info["is_toc"] or filter_info["is_noise"])


if __name__ == "__main__":
    main()
