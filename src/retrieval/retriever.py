"""
retriever.py
------------
Hybrid retriever that combines semantic vector search (ChromaDB) with
graph-based neighbourhood expansion to fetch the most relevant chunks
for a user query.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from src.models.schemas import ModalityType, QueryRequest, RetrievedChunk
from src.storage.graph_store import GraphStore
from src.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Two-stage retriever:

    1. **Vector stage** — queries ChromaDB for the top-K semantically
       similar chunks using dense embeddings.
    2. **Graph expansion stage** — for each vector hit, walks the
       evidence graph to surface related cross-modal chunks that the
       vector search may have missed.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        graph_depth: int = 1,
        graph_weight: float = 0.5,
    ) -> None:
        """
        Parameters
        ----------
        vector_store : VectorStore
            ChromaDB-backed semantic index.
        graph_store : GraphStore
            NetworkX evidence graph.
        graph_depth : int
            Hop depth for graph expansion.
        graph_weight : float
            Score multiplier applied to graph-expanded results (0–1).
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.graph_depth = graph_depth
        self.graph_weight = graph_weight

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(self, request: QueryRequest) -> List[RetrievedChunk]:
        """
        Run hybrid retrieval for a query request.

        Parameters
        ----------
        request : QueryRequest
            Query, top-k, modality filters, and graph flag.

        Returns
        -------
        List[RetrievedChunk]
            Deduplicated, ranked list of retrieved chunks.
        """
        # Stage 1: Vector search
        vector_hits = self.vector_store.query(
            query_text=request.query,
            top_k=request.top_k,
            modality_filter=request.modality_filter,
        )
        logger.info("Vector search returned %d hits.", len(vector_hits))

        if not request.use_graph:
            return vector_hits

        # Stage 2: Graph expansion
        all_chunks: Dict[str, RetrievedChunk] = {
            hit.chunk.chunk_id: hit for hit in vector_hits
        }

        for hit in vector_hits:
            node_id = hit.chunk.chunk_id
            neighbours = self.graph_store.get_neighbors(
                node_id, depth=self.graph_depth
            )
            for neighbour in neighbours:
                nid = neighbour.get("node_id", "")
                if nid and nid not in all_chunks:
                    # Re-use neighbour metadata to construct a lightweight chunk
                    from src.models.schemas import Chunk, ChunkType
                    chunk = Chunk(
                        chunk_id=nid,
                        source_file=neighbour.get("source_file", ""),
                        modality=neighbour.get("modality", ModalityType.TEXT),
                        chunk_type=neighbour.get("chunk_type", ChunkType.PDF_TEXT),
                        content=neighbour.get("content_summary", ""),
                        metadata=neighbour,
                    )
                    graph_score = round(hit.score * self.graph_weight, 4)
                    all_chunks[nid] = RetrievedChunk(
                        chunk=chunk, score=graph_score, source="graph"
                    )

        # Sort by score descending and return top_k
        ranked = sorted(all_chunks.values(), key=lambda r: r.score, reverse=True)
        logger.info(
            "Hybrid retrieval complete — %d results after graph expansion.",
            len(ranked),
        )
        return ranked[: request.top_k]
