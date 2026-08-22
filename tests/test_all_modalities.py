import io
import os
import shutil
import uuid
import struct
import zlib
import wave

import pytest
from backend.services.ingestion import ingest_file
from backend.services.text_processor import process_text
from backend.services.pdf_processor import process_pdf
from backend.services.image_processor import process_image


def _make_session():
    sid = f"test_{uuid.uuid4().hex[:8]}"
    os.makedirs(os.path.join("storage", "uploads", sid), exist_ok=True)
    return sid


def _write_minimal_png(path: str):
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def _write_minimal_wav(path: str):
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)


def _write_minimal_pdf(path: str):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello PDF test page one.")
    doc.save(path)
    doc.close()


def _write_minimal_txt(path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write("This is a test text file.\n" * 50)


@pytest.fixture(autouse=True)
def cleanup_sessions(request):
    sessions = []
    yield sessions
    for sid in sessions:
        shutil.rmtree(os.path.join("storage", "uploads", sid), ignore_errors=True)
        shutil.rmtree(os.path.join("storage", "processed", sid), ignore_errors=True)


def test_image_pipeline(cleanup_sessions):
    sid = _make_session()
    cleanup_sessions.append(sid)
    img_path = os.path.join("storage", "uploads", sid, "test.png")
    _write_minimal_png(img_path)

    result = ingest_file(sid, img_path)

    assert result["pipeline"] == "image"
    assert result["node_count"] >= 1
    image_nodes = [n for n in result["nodes"] if n["modality"] == "image"]
    assert len(image_nodes) == 1
    assert image_nodes[0]["media_path"] is not None
    assert image_nodes[0]["provenance"].startswith("original:")


def test_text_pipeline(cleanup_sessions):
    sid = _make_session()
    cleanup_sessions.append(sid)
    txt_path = os.path.join("storage", "uploads", sid, "test.txt")
    _write_minimal_txt(txt_path)

    result = ingest_file(sid, txt_path)

    assert result["pipeline"] == "text"
    assert result["node_count"] >= 1
    for node in result["nodes"]:
        assert node["modality"] == "text"
        assert node["text"]
        assert node["provenance"].startswith("txt:")


def test_pdf_pipeline(cleanup_sessions):
    sid = _make_session()
    cleanup_sessions.append(sid)
    pdf_path = os.path.join("storage", "uploads", sid, "test.pdf")
    _write_minimal_pdf(pdf_path)

    result = ingest_file(sid, pdf_path)

    assert result["pipeline"] == "pdf"
    assert result["node_count"] >= 1
    pdf_nodes = [n for n in result["nodes"] if n["modality"] in ("pdf_text", "pdf_ocr", "pdf_image_page")]
    assert len(pdf_nodes) >= 1
    for node in pdf_nodes:
        assert node["page_number"] is not None
        assert node["provenance"] is not None


def test_audio_pipeline(cleanup_sessions):
    sid = _make_session()
    cleanup_sessions.append(sid)
    wav_path = os.path.join("storage", "uploads", sid, "test.wav")
    _write_minimal_wav(wav_path)

    result = ingest_file(sid, wav_path)

    assert result["pipeline"] == "audio"
    assert isinstance(result["node_count"], int)
    assert isinstance(result["errors"], list)


def test_routing_by_extension():
    from backend.services.ingestion import (
        VIDEO_EXTENSIONS, AUDIO_EXTENSIONS,
        IMAGE_EXTENSIONS, PDF_EXTENSIONS, TEXT_EXTENSIONS,
    )
    assert ".mp4" in VIDEO_EXTENSIONS
    assert ".mov" in VIDEO_EXTENSIONS
    assert ".mp3" in AUDIO_EXTENSIONS
    assert ".wav" in AUDIO_EXTENSIONS
    assert ".png" in IMAGE_EXTENSIONS
    assert ".jpg" in IMAGE_EXTENSIONS
    assert ".jpeg" in IMAGE_EXTENSIONS
    assert ".pdf" in PDF_EXTENSIONS
    assert ".txt" in TEXT_EXTENSIONS


def test_node_schema_fields(cleanup_sessions):
    sid = _make_session()
    cleanup_sessions.append(sid)
    txt_path = os.path.join("storage", "uploads", sid, "schema_test.txt")
    _write_minimal_txt(txt_path)

    result = ingest_file(sid, txt_path)
    for node in result["nodes"]:
        assert "id" in node
        assert "session_id" in node
        assert "source_file" in node
        assert "modality" in node
        assert "provenance" in node
