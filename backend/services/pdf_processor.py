import os
import shutil
import uuid
from typing import List
from backend.models import MultimodalNode

def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None

def _ocr_image_bytes(image_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img).strip()
    except Exception:
        return ""

def process_pdf(file_path: str, session_id: str) -> List[MultimodalNode]:
    import fitz

    output_dir = os.path.join("storage", "processed", session_id, "pdf")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(file_path)
    nodes: List[MultimodalNode] = []

    try:
        doc = fitz.open(file_path)
    except Exception:
        raise ValueError(f"Cannot open PDF: {file_path}")

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_number = page_index + 1

            text = page.get_text("text").strip()

            if text:
                nodes.append(MultimodalNode(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    source_file=file_path,
                    modality="pdf_text",
                    text=text,
                    page_number=page_number,
                    provenance=f"pdf:{base_name}:page{page_number}",
                    metadata={"page_index": page_index, "extraction_method": "selectable_text"},
                ))
            else:
                if _tesseract_available():
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    ocr_text = _ocr_image_bytes(img_bytes)

                    img_filename = f"{os.path.splitext(base_name)[0]}_page{page_number}.png"
                    img_path = os.path.join(output_dir, img_filename)
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)

                    if ocr_text:
                        nodes.append(MultimodalNode(
                            id=uuid.uuid4().hex,
                            session_id=session_id,
                            source_file=file_path,
                            modality="pdf_ocr",
                            text=ocr_text,
                            page_number=page_number,
                            media_path=img_path,
                            provenance=f"pdf_ocr:{base_name}:page{page_number}",
                            metadata={
                                "page_index": page_index,
                                "extraction_method": "ocr",
                                "ocr_engine": "tesseract",
                                "rendered_image": img_path,
                            },
                        ))
                    else:
                        nodes.append(MultimodalNode(
                            id=uuid.uuid4().hex,
                            session_id=session_id,
                            source_file=file_path,
                            modality="pdf_image_page",
                            page_number=page_number,
                            media_path=img_path,
                            provenance=f"pdf_image:{base_name}:page{page_number}",
                            metadata={"page_index": page_index, "extraction_method": "render_only"},
                        ))
    finally:
        doc.close()

    return nodes
