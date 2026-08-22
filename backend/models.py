from typing import Optional
from pydantic import BaseModel

class MultimodalNode(BaseModel):
    id: str
    session_id: str
    source_file: str
    timestamp: float
    end_timestamp: Optional[float] = None
    media_path: Optional[str] = None
    text: Optional[str] = None
    modality: str
    confidence: Optional[float] = None
