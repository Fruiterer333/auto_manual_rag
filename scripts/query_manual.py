import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.chains.qa_chain import QAChain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a question against the manual index.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    response = QAChain().answer(question=args.question, top_k=args.top_k)

    print(f"问题：{response.question}")
    print(f"回答：{response.answer}")
    print("引用：")
    for citation in response.citations:
        print(f"- page={citation.page} chunk_id={citation.chunk_id}")
        print(f"  quote={citation.quote}")


if __name__ == "__main__":
    main()
