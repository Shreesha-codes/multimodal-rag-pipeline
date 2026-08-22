import os
import uuid
from typing import List
from backend.models import MultimodalNode
from backend.services.video_processor import extract_audio_from_video, extract_frames
from backend.services.audio_processor import transcribe_audio

def process_file(file_path: str, session_id: str) -> List[MultimodalNode]:
    ext = os.path.splitext(file_path)[1].lower()
    nodes = []
    
    if ext in [".mp4", ".mov"]:
        try:
            frames = extract_frames(file_path, session_id)
            for timestamp, frame_path in frames:
                nodes.append(MultimodalNode(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    source_file=file_path,
                    timestamp=timestamp,
                    media_path=frame_path,
                    modality="video_frame"
                ))
        except Exception:
            pass
            
        try:
            audio_path = extract_audio_from_video(file_path, session_id)
            if audio_path and os.path.exists(audio_path):
                audio_nodes = transcribe_audio(audio_path, session_id)
                nodes.extend(audio_nodes)
        except Exception:
            pass
            
    elif ext in [".mp3", ".wav"]:
        try:
            audio_nodes = transcribe_audio(file_path, session_id)
            nodes.extend(audio_nodes)
        except Exception:
            pass
            
    return nodes
