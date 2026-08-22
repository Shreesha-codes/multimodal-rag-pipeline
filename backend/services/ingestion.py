import os
import uuid
from typing import List, Dict, Any
from backend.models import MultimodalNode
from backend.services.video_processor import extract_audio_from_video, extract_frames
from backend.services.audio_processor import transcribe_audio
from backend.services.image_processor import process_image
from backend.services.pdf_processor import process_pdf
from backend.services.text_processor import process_text

VIDEO_EXTENSIONS = {".mp4", ".mov"}
AUDIO_EXTENSIONS = {".mp3", ".wav"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".txt"}

def ingest_file(session_id: str, file_path: str) -> Dict[str, Any]:
    ext = os.path.splitext(file_path)[1].lower()
    nodes: List[MultimodalNode] = []
    errors: List[str] = []
    pipeline: str = "unknown"

    if ext in VIDEO_EXTENSIONS:
        pipeline = "video"
        try:
            frames = extract_frames(file_path, session_id)
            for timestamp, frame_path in frames:
                vision_data = process_image(frame_path)
                nodes.append(MultimodalNode(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    source_file=file_path,
                    modality="video_frame",
                    timestamp=timestamp,
                    media_path=frame_path,
                    provenance=f"video_frame:{os.path.basename(file_path)}:{timestamp:.2f}",
                    ocr_text=vision_data.get("ocr_text"),
                    visual_summary=vision_data.get("visual_summary"),
                    entities=vision_data.get("entities"),
                    diagram_present=vision_data.get("diagram_present"),
                    visual_relationships=vision_data.get("visual_relationships")
                ))
        except Exception as e:
            errors.append(f"frame_extraction: {str(e)}")

        try:
            audio_path = extract_audio_from_video(file_path, session_id)
            if audio_path and os.path.exists(audio_path):
                audio_nodes = transcribe_audio(audio_path, session_id)
                nodes.extend(audio_nodes)
        except Exception as e:
            errors.append(f"audio_extraction: {str(e)}")

    elif ext in AUDIO_EXTENSIONS:
        pipeline = "audio"
        try:
            audio_nodes = transcribe_audio(file_path, session_id)
            nodes.extend(audio_nodes)
        except Exception as e:
            errors.append(f"transcription: {str(e)}")

    elif ext in IMAGE_EXTENSIONS:
        pipeline = "image"
        try:
            vision_data = process_image(file_path)
            nodes.append(MultimodalNode(
                id=uuid.uuid4().hex,
                session_id=session_id,
                source_file=file_path,
                modality="image",
                timestamp=0.0,
                media_path=file_path,
                ocr_text=vision_data.get("ocr_text"),
                visual_summary=vision_data.get("visual_summary"),
                entities=vision_data.get("entities"),
                diagram_present=vision_data.get("diagram_present"),
                visual_relationships=vision_data.get("visual_relationships")
            ))
        except Exception as e:
            errors.append(f"image_processing: {str(e)}")

    elif ext in PDF_EXTENSIONS:
        pipeline = "pdf"
        try:
            pdf_nodes = process_pdf(file_path, session_id)
            nodes.extend(pdf_nodes)
        except Exception as e:
            errors.append(f"pdf_processing: {str(e)}")

    elif ext in TEXT_EXTENSIONS:
        pipeline = "text"
        try:
            text_nodes = process_text(file_path, session_id)
            nodes.extend(text_nodes)
        except Exception as e:
            errors.append(f"text_processing: {str(e)}")

    return {
        "session_id": session_id,
        "file_path": file_path,
        "pipeline": pipeline,
        "node_count": len(nodes),
        "nodes": [n.model_dump() for n in nodes],
        "errors": errors,
    }


def process_file(file_path: str, session_id: str) -> List[MultimodalNode]:
    result = ingest_file(session_id, file_path)
    return [MultimodalNode(**n) for n in result["nodes"]]
