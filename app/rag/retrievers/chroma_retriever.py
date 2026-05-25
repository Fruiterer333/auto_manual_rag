from pathlib import Path

import chromadb

from app.core.config import Settings
from app.data.schemas.models import Chunk, RetrievedChunk


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
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[self._chunk_to_metadata(chunk) for chunk in chunks],
        )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
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
            retrieved.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=self._distance_to_score(distance),
                )
            )

        return retrieved

    def reset_collection(self) -> None:
        if self._collection_exists():
            self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

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
            "content_type": chunk.content_type or "",
            "risk_level": chunk.risk_level or "",
        }
        for key, value in chunk.metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
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
            content_type=str(metadata.get("content_type") or "") or None,
            risk_level=str(metadata.get("risk_level") or "") or None,
            metadata={
                key: value
                for key, value in metadata.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            },
        )

    def _distance_to_score(self, distance: object) -> float | None:
        if isinstance(distance, (int, float)):
            return 1.0 - float(distance)
        return None
