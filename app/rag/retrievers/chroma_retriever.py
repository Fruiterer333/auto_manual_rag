from pathlib import Path

import chromadb

from app.core.config import Settings
from app.core.logger import get_logger
from app.data.schemas.models import Chunk, RetrievedChunk


logger = get_logger(__name__)


class ChromaRetriever:
    """Persistent Chroma retriever for manual chunks."""

    def __init__(
        self,
        settings: Settings,
        collection_name: str = "auto_manual_chunks",
    ) -> None:
        self.settings = settings
        self.collection_name = collection_name
        Path(settings.CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        logger.info(
            "Initializing Chroma retriever: chroma_dir=%s collection=%s metric=cosine",
            settings.CHROMA_DIR,
            collection_name,
        )
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        logger.info("Adding chunks to Chroma: count=%s collection=%s", len(chunks), self.collection_name)
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            logger.warning("No chunks to add to Chroma")
            return

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[self._chunk_to_metadata(chunk) for chunk in chunks],
        )
        logger.info("Chunks added to Chroma: count=%s collection=%s", len(chunks), self.collection_name)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        logger.info("Searching Chroma: top_k=%s collection=%s", top_k, self.collection_name)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        if not distances:
            distances = [None] * len(ids)

        retrieved: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            chunk = self._metadata_to_chunk(chunk_id, text or "", metadata or {})
            retrieved_chunk = RetrievedChunk(
                chunk=chunk,
                score=self._distance_to_score(distance),
                distance=self._normalize_distance(distance),
            )
            retrieved.append(retrieved_chunk)
            logger.info(
                "Search result: rank=%s page=%s score=%s distance=%s chunk_id=%s",
                len(retrieved),
                chunk.page,
                retrieved_chunk.score,
                retrieved_chunk.distance,
                chunk.chunk_id,
            )
            logger.debug(
                "Search result preview: rank=%s preview=%s",
                len(retrieved),
                chunk.text[:80].replace("\n", " "),
            )

        logger.info("Chroma search completed: returned=%s", len(retrieved))
        return retrieved

    def reset_collection(self) -> None:
        logger.info("Resetting Chroma collection: collection=%s", self.collection_name)
        if self._collection_exists():
            self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def find_neighbor_chunks(
        self,
        chunk: Chunk,
        max_neighbors: int = 1,
    ) -> list[RetrievedChunk]:
        if max_neighbors <= 0:
            return []

        chunk_index = self._metadata_int(chunk, "chunk_index")
        if chunk_index is None:
            return []

        try:
            results = self.collection.get(
                where={"source_file": chunk.source_file},
                include=["documents", "metadatas"],
            )
        except Exception:
            logger.exception("Failed to lookup neighbor chunks: chunk_id=%s", chunk.chunk_id)
            return []

        ids = results.get("ids", [])
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        candidates: list[Chunk] = []
        for chunk_id, text, metadata in zip(ids, documents, metadatas, strict=False):
            if chunk_id == chunk.chunk_id:
                continue
            candidate = self._metadata_to_chunk(chunk_id, text or "", metadata or {})
            if self._is_neighbor_candidate(chunk, candidate, chunk_index):
                candidates.append(candidate)

        candidates.sort(
            key=lambda candidate: abs(
                (self._metadata_int(candidate, "chunk_index") or chunk_index) - chunk_index
            )
        )
        neighbors = [
            RetrievedChunk(chunk=candidate, is_expanded_neighbor=True)
            for candidate in candidates[:max_neighbors]
        ]
        logger.info(
            "Neighbor lookup completed: base_chunk_id=%s neighbors=%s",
            chunk.chunk_id,
            [neighbor.chunk.chunk_id for neighbor in neighbors],
        )
        return neighbors

    def _collection_exists(self) -> bool:
        for collection in self.client.list_collections():
            name = getattr(collection, "name", collection)
            if name == self.collection_name:
                return True
        return False

    def _chunk_to_metadata(self, chunk: Chunk) -> dict[str, str | int | float | bool]:
        metadata: dict[str, str | int | float | bool] = {
            "source_file": chunk.source_file,
            "page": chunk.page if chunk.page is not None else -1,
            "doc_id": chunk.doc_id,
            "chapter": chunk.chapter or "",
            "section": chunk.section or "",
            "subsection": chunk.subsection or "",
            "content_type": chunk.content_type or "",
            "risk_level": chunk.risk_level or "",
            "start_page": self._metadata_value(chunk, "start_page", -1),
            "end_page": self._metadata_value(chunk, "end_page", -1),
            "heading_path": self._metadata_value(chunk, "heading_path", ""),
            "split_strategy": self._metadata_value(chunk, "split_strategy", ""),
            "has_warning": self._metadata_value(chunk, "has_warning", False),
            "has_caution": self._metadata_value(chunk, "has_caution", False),
            "has_note": self._metadata_value(chunk, "has_note", False),
            "is_procedure": self._metadata_value(chunk, "is_procedure", False),
            "source_pages": self._metadata_value(chunk, "source_pages", ""),
        }
        for key, value in chunk.metadata.items():
            sanitized = self._sanitize_metadata_value(value, key=key)
            if sanitized is not None:
                metadata[key] = sanitized
        return metadata

    def _metadata_to_chunk(
        self,
        chunk_id: str,
        text: str,
        metadata: dict,
    ) -> Chunk:
        page = metadata.get("page")
        return Chunk(
            chunk_id=chunk_id,
            doc_id=str(metadata.get("doc_id", "")),
            source_file=str(metadata.get("source_file", "")),
            page=page if isinstance(page, int) and page > 0 else None,
            text=text,
            chapter=str(metadata.get("chapter") or "") or None,
            section=str(metadata.get("section") or "") or None,
            subsection=str(metadata.get("subsection") or "") or None,
            content_type=str(metadata.get("content_type") or "") or None,
            risk_level=str(metadata.get("risk_level") or "") or None,
            metadata={
                key: value
                for key, value in metadata.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            },
        )

    def _is_neighbor_candidate(
        self,
        base_chunk: Chunk,
        candidate: Chunk,
        base_index: int,
    ) -> bool:
        candidate_index = self._metadata_int(candidate, "chunk_index")
        if candidate_index is None or candidate_index <= base_index:
            return False
        if candidate_index - base_index > 2:
            return False
        if candidate.source_file != base_chunk.source_file:
            return False
        if base_chunk.chapter and candidate.chapter != base_chunk.chapter:
            return False
        if base_chunk.section:
            if candidate.section != base_chunk.section:
                return False
        else:
            base_page = base_chunk.page or -999
            candidate_page = candidate.page or -999
            if abs(candidate_page - base_page) > 1:
                return False
        return True

    def _metadata_int(self, chunk: Chunk, key: str) -> int | None:
        value = chunk.metadata.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def _metadata_value(
        self,
        chunk: Chunk,
        key: str,
        default: str | int | float | bool,
    ) -> str | int | float | bool:
        value = chunk.metadata.get(key, default)
        sanitized = self._sanitize_metadata_value(value, key=key)
        return sanitized if sanitized is not None else default

    def _sanitize_metadata_value(
        self,
        value: object,
        key: str | None = None,
    ) -> str | int | float | bool | None:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            if key == "heading_path":
                return " > ".join(str(item) for item in value)
            return ",".join(str(item) for item in value)
        return str(value)

    def _distance_to_score(self, distance: object) -> float | None:
        normalized_distance = self._normalize_distance(distance)
        if normalized_distance is None:
            return None
        # Chroma cosine distance is smaller for more relevant chunks.
        # This score is based on cosine distance: higher score is more relevant.
        return 1.0 - normalized_distance

    def _normalize_distance(self, distance: object) -> float | None:
        if isinstance(distance, (int, float)):
            return float(distance)
        return None
