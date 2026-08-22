import os
import uuid
from typing import List
from backend.models import MultimodalNode

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100

def _chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def process_text(file_path: str, session_id: str) -> List[MultimodalNode]:
    base_name = os.path.basename(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        raise ValueError(f"Cannot read text file: {file_path}")

    content = content.strip()
    if not content:
        return []

    chunks = _chunk_text(content)
    nodes: List[MultimodalNode] = []

    for idx, chunk in enumerate(chunks):
        nodes.append(MultimodalNode(
            id=uuid.uuid4().hex,
            session_id=session_id,
            source_file=file_path,
            modality="text",
            text=chunk,
            provenance=f"txt:{base_name}:chunk{idx}",
            metadata={
                "chunk_index": idx,
                "chunk_total": len(chunks),
                "char_start": idx * (DEFAULT_CHUNK_SIZE - DEFAULT_CHUNK_OVERLAP),
            },
        ))

    return nodes
