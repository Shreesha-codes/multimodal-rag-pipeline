from typing import Optional, Dict, Any
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
