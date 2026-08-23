from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class MultimodalNode(BaseModel):
    id: str
    session_id: str
    source_file: str
    modality: str
    timestamp: float = 0.0
    end_timestamp: Optional[float] = None
    media_path: Optional[str] = None
    text: Optional[str] = None
    confidence: Optional[float] = None
    page_number: Optional[int] = None
    provenance: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ocr_text: Optional[str] = None
    visual_summary: Optional[str] = None
    entities: Optional[list] = None
    diagram_present: Optional[bool] = None
    visual_relationships: Optional[str] = None

class EvidenceItem(BaseModel):
    node_id: str
    modality: str
    score: float
    source_file: str
    media_path: Optional[str] = None
    timestamp: Optional[float] = None
    page: Optional[int] = None
    text_content: Optional[str] = None
    relationship_path: Optional[str] = None
    is_primary: bool = True

class EvidenceBundle(BaseModel):
    query: str
    session_id: str
    evidence: List[EvidenceItem]

class FinalResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    confidence: str
    evidence_bundle: EvidenceBundle

class ComparisonMetrics(BaseModel):
    baseline_modality_coverage: List[str]
    multimodal_modality_coverage: List[str]
    baseline_source_coverage: int
    multimodal_source_coverage: int

class ComparisonResult(BaseModel):
    query: str
    session_id: str
    baseline: FinalResponse
    multimodal: FinalResponse
    metrics: ComparisonMetrics
