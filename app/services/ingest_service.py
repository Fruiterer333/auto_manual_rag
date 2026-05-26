from dataclasses import dataclass
from collections import Counter
from statistics import mean
from time import perf_counter

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.data.cleaners.text_cleaner import clean_text
from app.data.loaders.pdf_loader import PDFLoader
from app.data.parsers.manual_structure_parser import ManualStructureParser
from app.data.splitters.manual_splitter import ManualTextSplitter
from app.data.splitters.manual_structure_splitter import ManualStructureSplitter
from app.data.schemas.models import Chunk
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.retrievers.chroma_retriever import ChromaRetriever


logger = get_logger(__name__)


@dataclass(frozen=True)
class IngestResult:
    success: bool
    pages: int
    chunks: int
    message: str


def ingest_manual(
    file_path: str,
    rebuild: bool = True,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    settings: Settings | None = None,
) -> IngestResult:
    start_time = perf_counter()
    settings = settings or get_settings()
    logger.info(
        "Ingest started: file_path=%s rebuild=%s chunk_size=%s chunk_overlap=%s",
        file_path,
        rebuild,
        chunk_size,
        chunk_overlap,
    )

    loader = PDFLoader()
    documents = loader.load(file_path)
    logger.info("Loaded pages: %s", len(documents))

    cleaned_documents = [
        document.model_copy(update={"text": clean_text(document.text)})
        for document in documents
    ]
    logger.info("Cleaned documents: %s", len(cleaned_documents))

    parser = ManualStructureParser()
    manual_blocks = parser.parse(cleaned_documents)
    logger.info("Manual parser generated blocks: %s", len(manual_blocks))

    manual_splitter = ManualStructureSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = manual_splitter.split_blocks(manual_blocks)
    fallback_used = not chunks
    if fallback_used:
        logger.warning("Manual-aware split produced no chunks; falling back to fixed splitter")
        splitter = ManualTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_documents(cleaned_documents)

    logger.info(
        "Created chunks: %s fallback_used=%s content_type=%s risk_level=%s length_stats=%s",
        len(chunks),
        fallback_used,
        _distribution(chunks, "content_type"),
        _distribution(chunks, "risk_level"),
        _length_stats(chunks),
    )

    embedding_client = LocalEmbeddingClient(settings)
    logger.info("Embedding model: %s", settings.EMBEDDING_MODEL_NAME)
    embeddings = embedding_client.embed_texts([chunk.text for chunk in chunks])
    logger.info("Created embeddings: %s", len(embeddings))

    retriever = ChromaRetriever(settings)
    logger.info("Chroma dir: %s", settings.CHROMA_DIR)
    if rebuild:
        retriever.reset_collection()
    retriever.add_chunks(chunks, embeddings)
    logger.info("Chroma write completed: chunks=%s", len(chunks))
    logger.info("Ingest completed: elapsed=%.2fs", perf_counter() - start_time)

    return IngestResult(
        success=True,
        pages=len(documents),
        chunks=len(chunks),
        message="Manual index built successfully",
    )


def _distribution(chunks: list[Chunk], field_name: str) -> dict[str, int]:
    return dict(Counter(getattr(chunk, field_name) or "unknown" for chunk in chunks))


def _length_stats(chunks: list[Chunk]) -> dict[str, float | int]:
    if not chunks:
        return {"min": 0, "max": 0, "avg": 0.0}
    lengths = [len(chunk.text) for chunk in chunks]
    return {
        "min": min(lengths),
        "max": max(lengths),
        "avg": round(mean(lengths), 1),
    }
