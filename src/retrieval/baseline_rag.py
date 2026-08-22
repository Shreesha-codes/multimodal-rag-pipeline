"""
baseline_rag.py
---------------
A simple baseline RAG implementation using vector-search only (no graph).
Useful for benchmarking the multimodal hybrid pipeline against a naive approach.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from src.models.schemas import QueryRequest, QueryResponse, RetrievedChunk
from src.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class BaselineRAG:
    """
    Vanilla RAG pipeline:
    1. Embed the query.
    2. Retrieve top-K chunks from the vector store.
    3. Concatenate chunk texts into a context window.
    4. Call an LLM to generate an answer.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_model: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
        max_context_tokens: int = 4096,
    ) -> None:
        self.vector_store = vector_store
        self.llm_model = llm_model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.max_context_tokens = max_context_tokens
        self._llm = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_llm(self):
        if self._llm is None:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._llm = genai.GenerativeModel(self.llm_model)
        return self._llm

    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        """Concatenate retrieved chunks into a context string."""
        parts = []
        for i, hit in enumerate(chunks, start=1):
            source = hit.chunk.source_file or "unknown"
            modality = hit.chunk.modality
            parts.append(
                f"[{i}] ({modality} | {source})\n{hit.chunk.content}"
            )
        return "\n\n---\n\n".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def answer(self, request: QueryRequest) -> QueryResponse:
        """
        Run the baseline RAG pipeline for a query.

        Parameters
        ----------
        request : QueryRequest
            Incoming query with retrieval parameters.

        Returns
        -------
        QueryResponse
            Generated answer with supporting chunks.
        """
        hits = self.vector_store.query(
            query_text=request.query,
            top_k=request.top_k,
            modality_filter=request.modality_filter,
        )

        if not hits:
            return QueryResponse(
                query=request.query,
                answer="I could not find any relevant information to answer your question.",
                retrieved_chunks=[],
            )

        context = self._build_context(hits)
        prompt = (
            "You are a helpful assistant. Use ONLY the following retrieved context "
            "to answer the question. If the answer is not in the context, say so.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {request.query}\n\nANSWER:"
        )

        llm = self._get_llm()
        response = llm.generate_content(prompt)
        answer_text = response.text.strip()

        sources = list({hit.chunk.source_file for hit in hits})

        return QueryResponse(
            query=request.query,
            answer=answer_text,
            retrieved_chunks=hits,
            sources=sources,
        )
