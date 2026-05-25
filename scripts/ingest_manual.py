import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.ingest_service import ingest_manual


logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Chroma index for a manual PDF.")
    parser.add_argument("--file-path", default="data/raw/train_a.pdf")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    result = ingest_manual(
        file_path=args.file_path,
        rebuild=args.rebuild,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        settings=settings,
    )
    logger.info("Loaded pages: %s", result.pages)
    logger.info("Chunks: %s", result.chunks)
    logger.info("Embedding model: %s", settings.EMBEDDING_MODEL_NAME)
    logger.info("Chroma dir: %s", settings.CHROMA_DIR)
    logger.info("Rebuild: %s", args.rebuild)
    logger.info(result.message)


if __name__ == "__main__":
    main()
