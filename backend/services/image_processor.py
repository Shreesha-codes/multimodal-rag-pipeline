import os
import shutil
import uuid
from typing import List
from backend.models import MultimodalNode

def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None

def _run_ocr(image_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        return pytesseract.image_to_string(img).strip()
    except Exception:
        return ""

def process_image(file_path: str, session_id: str) -> List[MultimodalNode]:
    from PIL import Image

    try:
        img = Image.open(file_path)
        img.verify()
    except Exception:
        raise ValueError(f"Invalid or corrupt image file: {file_path}")

    output_dir = os.path.join("storage", "processed", session_id, "images")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(file_path)
    stored_path = os.path.join(output_dir, base_name)
    if not os.path.exists(stored_path):
        shutil.copy2(file_path, stored_path)

    with Image.open(file_path) as img:
        width, height = img.size
        fmt = img.format or "UNKNOWN"


    nodes: List[MultimodalNode] = []

    image_node = MultimodalNode(
        id=uuid.uuid4().hex,
        session_id=session_id,
        source_file=file_path,
        modality="image",
        media_path=stored_path,
        provenance=f"original:{base_name}",
        metadata={"width": width, "height": height, "format": fmt},
    )
    nodes.append(image_node)

    if _tesseract_available():
        ocr_text = _run_ocr(file_path)
        if ocr_text:
            ocr_node = MultimodalNode(
                id=uuid.uuid4().hex,
                session_id=session_id,
                source_file=file_path,
                modality="ocr",
                text=ocr_text,
                media_path=stored_path,
                provenance=f"ocr:{base_name}",
                metadata={"ocr_engine": "tesseract", "source_image": stored_path},
            )
            nodes.append(ocr_node)

    return nodes
