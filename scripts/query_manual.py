import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.rag.chains.qa_chain import QAChain
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.retrievers.chroma_retriever import ChromaRetriever
from app.rag.utils.citation_utils import build_relevant_quote


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a question against the manual index.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--debug-retrieval", action="store_true")
    parser.add_argument("--show-full-chunk", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.debug_retrieval:
        debug_retrieval(
            question=args.question,
            top_k=args.top_k,
            show_full_chunk=args.show_full_chunk,
        )
        return

    response = QAChain().answer(question=args.question, top_k=args.top_k)

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


def debug_retrieval(question: str, top_k: int, show_full_chunk: bool = False) -> None:
    settings = get_settings()
    embedding_client = LocalEmbeddingClient(settings)
    retriever = ChromaRetriever(settings)
    query_embedding = embedding_client.embed_query(question)
    results = retriever.search(query_embedding=query_embedding, top_k=top_k)

    print(f"问题：{question}")
    print("检索结果：")
    for rank, result in enumerate(results, start=1):
        chunk = result.chunk
        score = result.score if result.score is not None else "N/A"
        distance = result.distance if result.distance is not None else "N/A"
        chunk_text = chunk.text if show_full_chunk else chunk.text[:300].replace("\n", " ")
        quote = build_relevant_quote(question, chunk.text)
        print(f"\nrank={rank}")
        print(f"score={score}")
        print(f"distance={distance}")
        print(f"page={chunk.page}")
        print(f"chunk_id={chunk.chunk_id}")
        print(f"source_file={chunk.source_file}")
        label = "full_chunk" if show_full_chunk else "text_preview"
        print(f"{label}={chunk_text}")
        print(f"relevant_quote={quote}")


if __name__ == "__main__":
    main()
