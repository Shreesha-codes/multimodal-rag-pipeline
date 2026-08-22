import uuid
from typing import List
from faster_whisper import WhisperModel
from backend.models import MultimodalNode

def transcribe_audio(audio_path: str, session_id: str) -> List[MultimodalNode]:
    try:
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
    except Exception:
        raise RuntimeError("Failed to load WhisperModel")
        
    nodes = []
    
    try:
        segments, _ = model.transcribe(audio_path, beam_size=1)
        
        for segment in segments:
            if not segment.text.strip():
                continue
                
            nodes.append(MultimodalNode(
                id=uuid.uuid4().hex,
                session_id=session_id,
                source_file=audio_path,
                timestamp=segment.start,
                end_timestamp=segment.end,
                text=segment.text.strip(),
                modality="audio",
                confidence=None
            ))
            
        return nodes
    except Exception:
        raise RuntimeError("Whisper transcription failed")
