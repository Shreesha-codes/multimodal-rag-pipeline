"""
aligner.py
----------
Aligns multimodal chunks across modalities by linking semantically related
content in the graph store. For example, a transcript segment that discusses
the same topic as a video frame will be connected by an 'aligned' edge.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from src.models.schemas import Chunk, GraphEdge, GraphNode, ModalityType
from src.storage.graph_store import GraphStore

logger = logging.getLogger(__name__)

# Minimum cosine similarity threshold to create an alignment edge
ALIGNMENT_THRESHOLD = 0.75


class Aligner:
    """
    Cross-modal alignment layer.

    Reads chunks from different modalities, computes pairwise similarities,
    and creates 'aligned' edges in the GraphStore between sufficiently
    similar chunks from different modalities.
    """

    def __init__(
        self,
        graph_store: GraphStore,
        threshold: float = ALIGNMENT_THRESHOLD,
    ) -> None:
        self.graph_store = graph_store
        self.threshold = threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_chunks(self, chunks: List[Chunk]) -> None:
        """
        Add chunks as nodes to the graph store.

        Parameters
        ----------
        chunks : List[Chunk]
            Chunks to register as graph nodes.
        """
        for chunk in chunks:
            node = GraphNode(
                node_id=chunk.chunk_id,
                label=chunk.chunk_type,
                modality=chunk.modality,
                content_summary=chunk.content[:200],
                metadata={"source_file": chunk.source_file, **chunk.metadata},
            )
            self.graph_store.add_node(node)
        logger.info("Registered %d chunks as graph nodes.", len(chunks))

    def align(self, chunks_a: List[Chunk], chunks_b: List[Chunk]) -> int:
        """
        Find cross-modal alignments between two lists of chunks using
        embedding cosine similarity and add edges to the graph.

        Parameters
        ----------
        chunks_a : List[Chunk]
            Chunks from modality A (must have embeddings set).
        chunks_b : List[Chunk]
            Chunks from modality B (must have embeddings set).

        Returns
        -------
        int
            Number of alignment edges created.
        """
        pairs = self._find_similar_pairs(chunks_a, chunks_b)
        count = 0
        for chunk_a, chunk_b, score in pairs:
            if score >= self.threshold:
                edge = GraphEdge(
                    source_id=chunk_a.chunk_id,
                    target_id=chunk_b.chunk_id,
                    relation="aligned",
                    weight=round(score, 4),
                )
                self.graph_store.add_edge(edge)
                count += 1

        logger.info(
            "Alignment complete — %d cross-modal edges created (threshold=%.2f).",
            count, self.threshold,
        )
        return count

    def link_sequential(self, chunks: List[Chunk], relation: str = "follows") -> None:
        """
        Link chunks in sequence (e.g. transcript segments, PDF pages).

        Parameters
        ----------
        chunks : List[Chunk]
            Ordered list of chunks.
        relation : str
            Edge relation label.
        """
        ids = [c.chunk_id for c in chunks]
        self.graph_store.link_sequential(ids, relation=relation)
        logger.info("Linked %d chunks sequentially with relation '%s'.", len(chunks), relation)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""
        import math
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a ** 2 for a in vec_a))
        norm_b = math.sqrt(sum(b ** 2 for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _find_similar_pairs(
        self,
        chunks_a: List[Chunk],
        chunks_b: List[Chunk],
    ) -> List[Tuple[Chunk, Chunk, float]]:
        """Return (chunk_a, chunk_b, similarity) pairs above threshold."""
        pairs: List[Tuple[Chunk, Chunk, float]] = []
        for ca in chunks_a:
            if ca.embedding is None:
                continue
            for cb in chunks_b:
                if cb.embedding is None:
                    continue
                sim = self._cosine_similarity(ca.embedding, cb.embedding)
                if sim >= self.threshold:
                    pairs.append((ca, cb, sim))
        return sorted(pairs, key=lambda x: x[2], reverse=True)
