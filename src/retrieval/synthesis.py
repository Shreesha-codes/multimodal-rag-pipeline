"""
synthesis.py
------------
Answer synthesis layer for the multimodal RAG pipeline.
Formats retrieved cross-modal chunks into a structured prompt and
calls a multimodal LLM to generate a grounded, cited answer.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from src.models.schemas import QueryRequest, QueryResponse, RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a multimodal research assistant with access to content \
extracted from videos, audio transcripts, PDF documents, and images.

When answering, follow these rules:
1. Ground every claim in the provided context — do not hallucinate.
2. Cite the source and modality of information (e.g., "[Video frame @ 12.5s]", "[PDF p.3]").
3. If the context is insufficient, clearly state what is missing.
4. Structure longer answers with clear headings.
5. Be concise but complete.
"""


class Synthesizer:
    """
    Generates a final, cited answer by sending retrieved multimodal
    chunks to a generative LLM.
    """

    def __init__(
        self,
        llm_model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        llm_model : str
            Gemini model identifier.
        api_key : str, optional
            Google AI API key. Falls back to GOOGLE_API_KEY env var.
        """
        self.llm_model = llm_model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._llm = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_llm(self):
        if self._llm is None:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._llm = genai.GenerativeModel(
                self.llm_model,
                system_instruction=SYSTEM_PROMPT,
            )
        return self._llm

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Build a rich context block from retrieved chunks."""
        parts: List[str] = []
        for i, hit in enumerate(chunks, start=1):
            c = hit.chunk
            source_label = self._build_source_label(hit)
            parts.append(
                f"[CHUNK {i}] Source: {source_label} | Score: {hit.score:.3f}\n"
                f"{c.content}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _build_source_label(hit: RetrievedChunk) -> str:
        """Build a human-readable source label from chunk metadata."""
        c = hit.chunk
        label = c.source_file or "unknown"
        meta = c.metadata

        if c.modality == "video" and "timestamp_sec" in meta:
            label = f"Video frame @ {meta['timestamp_sec']}s"
        elif c.modality == "audio" and "start_sec" in meta:
            label = f"Transcript [{meta['start_sec']}s – {meta.get('end_sec', '?')}s]"
        elif c.modality == "pdf" and "page_number" in meta:
            label = f"{c.source_file} — p.{meta['page_number']}"
        elif c.modality == "image":
            label = f"Image: {c.source_file}"

        return label

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        request: QueryRequest,
        retrieved_chunks: List[RetrievedChunk],
    ) -> QueryResponse:
        """
        Synthesise a final answer from retrieved chunks.

        Parameters
        ----------
        request : QueryRequest
            Original user query.
        retrieved_chunks : List[RetrievedChunk]
            Ranked chunks from the hybrid retriever.

        Returns
        -------
        QueryResponse
            Structured response with answer, citations, and source list.
        """
        if not retrieved_chunks:
            return QueryResponse(
                query=request.query,
                answer="No relevant information was found in the knowledge base.",
                retrieved_chunks=[],
                sources=[],
            )

        context = self._format_context(retrieved_chunks)
        prompt = (
            f"RETRIEVED CONTEXT:\n{context}\n\n"
            f"USER QUESTION: {request.query}"
        )

        llm = self._get_llm()
        logger.info("Calling LLM '%s' for synthesis…", self.llm_model)
        response = llm.generate_content(prompt)
        answer = response.text.strip()

        sources = list({self._build_source_label(h) for h in retrieved_chunks})
        confidence = (
            sum(h.score for h in retrieved_chunks) / len(retrieved_chunks)
            if retrieved_chunks
            else None
        )

        return QueryResponse(
            query=request.query,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            sources=sources,
            confidence=round(confidence, 4) if confidence else None,
        )
