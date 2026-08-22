"""
schemas.py
----------
Pydantic data models (schemas) for the multimodal RAG pipeline.
Defines structured types for documents, chunks, embeddings, and query results.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModalityType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"


class ChunkType(str, Enum):
    TRANSCRIPT = "transcript"
    FRAME_DESCRIPTION = "frame_description"
    PDF_TEXT = "pdf_text"
    PDF_IMAGE = "pdf_image"
    IMAGE_DESCRIPTION = "image_description"


# ---------------------------------------------------------------------------
# Core chunk / document schemas
# ---------------------------------------------------------------------------

class Chunk(BaseModel):
    """A single unit of retrieved / ingested content."""

    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_file: str = Field(..., description="Original file name or path")
    modality: ModalityType
    chunk_type: ChunkType
    content: str = Field(..., description="Text content or description")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = Field(default=None, exclude=True)

    class Config:
        use_enum_values = True


class VideoFrame(BaseModel):
    """Metadata for an extracted video frame."""

    frame_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_video: str
    timestamp_sec: float
    frame_path: str
    description: Optional[str] = None


class AudioSegment(BaseModel):
    """A transcribed audio segment."""

    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_audio: str
    start_sec: float
    end_sec: float
    transcript: str
    speaker: Optional[str] = None


class PDFPage(BaseModel):
    """Extracted content from a single PDF page."""

    page_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_pdf: str
    page_number: int
    text: str
    image_paths: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Query / retrieval schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Incoming query from the user."""

    query: str = Field(..., description="Natural-language question")
    top_k: int = Field(default=5, ge=1, le=50)
    modality_filter: Optional[List[ModalityType]] = None
    use_graph: bool = Field(default=True)


class RetrievedChunk(BaseModel):
    """A chunk returned by the retriever, with a relevance score."""

    chunk: Chunk
    score: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(default="vector", description="vector | graph | hybrid")


class QueryResponse(BaseModel):
    """Final synthesized answer returned to the user."""

    query: str
    answer: str
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None


# ---------------------------------------------------------------------------
# Graph schemas
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    """A node in the evidence knowledge graph."""

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    modality: ModalityType
    content_summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed edge between two graph nodes."""

    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    relation: str = Field(..., description="e.g. 'mentions', 'follows', 'derived_from'")
    weight: float = Field(default=1.0)


class EvidenceGraph(BaseModel):
    """Full knowledge graph containing nodes and edges."""

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
