"""
vector_store.py
---------------
Manages storage and retrieval of chunk embeddings using ChromaDB.
Supports adding, updating, and querying chunks by semantic similarity.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from src.models.schemas import Chunk, ModalityType, RetrievedChunk

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION = "multimodal_rag"
DEFAULT_CHROMA_DIR = "chroma_db"


class VectorStore:
    """
    Wraps ChromaDB to provide a simple interface for:
    - Adding embedded chunks
    - Querying by text similarity
    - Filtering by modality
    """

    def __init__(
        self,
        persist_dir: str = DEFAULT_CHROMA_DIR,
        collection_name: str = DEFAULT_COLLECTION,
        embedding_model: str = "text-embedding-004",
        api_key: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        persist_dir : str
            Path where ChromaDB persists its data on disk.
        collection_name : str
            Name of the ChromaDB collection.
        embedding_model : str
            Google embedding model identifier.
        api_key : str, optional
            Google AI API key. Falls back to GOOGLE_API_KEY env var.
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_collection(self):
        if self._collection is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB collection '%s' ready (%d docs).",
                self.collection_name,
                self._collection.count(),
            )
        return self._collection

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings via Google's embedding API."""
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=self.api_key)
        result = genai.embed_content(
            model=f"models/{self.embedding_model}",
            content=texts,
            task_type="retrieval_document",
        )
        return result["embedding"] if isinstance(texts, str) else result["embedding"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """
        Embed and store a list of chunks in ChromaDB.

        Parameters
        ----------
        chunks : List[Chunk]
            Chunks to store. Content field is used for embedding.
        """
        if not chunks:
            return

        collection = self._get_collection()
        texts = [c.content for c in chunks]
        embeddings = self._embed(texts)

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "source_file": c.source_file,
                "modality": c.modality,
                "chunk_type": c.chunk_type,
                **{k: str(v) for k, v in c.metadata.items()},
            }
            for c in chunks
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info("Added %d chunks to vector store.", len(chunks))

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        modality_filter: Optional[List[ModalityType]] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve the most semantically similar chunks.

        Parameters
        ----------
        query_text : str
            Natural-language query string.
        top_k : int
            Number of results to return.
        modality_filter : List[ModalityType], optional
            Restrict results to specific modalities.

        Returns
        -------
        List[RetrievedChunk]
            Ranked list of retrieved chunks with scores.
        """
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=self.api_key)
        query_embedding = genai.embed_content(
            model=f"models/{self.embedding_model}",
            content=query_text,
            task_type="retrieval_query",
        )["embedding"]

        where_clause = None
        if modality_filter:
            where_clause = {"modality": {"$in": [m.value for m in modality_filter]}}

        collection = self._get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count() or 1),
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        retrieved: List[RetrievedChunk] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunk = Chunk(
                source_file=meta.get("source_file", ""),
                modality=meta.get("modality", "text"),
                chunk_type=meta.get("chunk_type", "pdf_text"),
                content=doc,
                metadata=meta,
            )
            # ChromaDB cosine distance → similarity score
            score = max(0.0, 1.0 - dist)
            retrieved.append(RetrievedChunk(chunk=chunk, score=round(score, 4), source="vector"))

        return retrieved

    def count(self) -> int:
        """Return total number of stored chunks."""
        return self._get_collection().count()

    def reset(self) -> None:
        """Delete all documents from the collection."""
        collection = self._get_collection()
        collection.delete(where={"modality": {"$ne": "__none__"}})
        logger.warning("Vector store collection '%s' cleared.", self.collection_name)
