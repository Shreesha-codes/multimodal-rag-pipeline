"""
run_pipeline.py
---------------
End-to-end ingestion script for the multimodal RAG pipeline.

Usage:
    python run_pipeline.py                    # process all raw files
    python run_pipeline.py --skip-video       # skip video extraction
    python run_pipeline.py --skip-audio       # skip audio transcription
    python run_pipeline.py --skip-vision      # skip vision analysis
"""

from __future__ import annotations

import argparse
import logging

from src.ingestion.audio_extractor import AudioExtractor
from src.ingestion.doc_extractor import DocExtractor
from src.ingestion.video_extractor import VideoExtractor
from src.ingestion.vision_analyzer import VisionAnalyzer
from src.models.schemas import (
    Chunk, ChunkType, ModalityType, AudioSegment
)
from src.storage.aligner import Aligner
from src.storage.graph_store import GraphStore
from src.storage.vector_store import VectorStore
from src.utils.helpers import discover_raw_inputs, setup_logging, timer, load_env

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def audio_segments_to_chunks(segments, source_file: str):
    return [
        Chunk(
            source_file=source_file,
            modality=ModalityType.AUDIO,
            chunk_type=ChunkType.TRANSCRIPT,
            content=seg.transcript,
            metadata={
                "start_sec": seg.start_sec,
                "end_sec": seg.end_sec,
                "speaker": seg.speaker or "",
            },
        )
        for seg in segments
    ]


def pdf_pages_to_chunks(pages, source_file: str):
    chunks = []
    for page in pages:
        if page.text.strip():
            chunks.append(
                Chunk(
                    source_file=source_file,
                    modality=ModalityType.PDF,
                    chunk_type=ChunkType.PDF_TEXT,
                    content=page.text,
                    metadata={"page_number": page.page_number},
                )
            )
    return chunks


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> None:
    load_env()
    setup_logging()

    raw = discover_raw_inputs("data/raw")
    logger.info(
        "Discovered — videos: %d | PDFs: %d | images: %d",
        len(raw["videos"]), len(raw["pdfs"]), len(raw["images"]),
    )

    # Initialise components
    video_extractor = VideoExtractor()
    audio_extractor = AudioExtractor()
    doc_extractor = DocExtractor()
    vision_analyzer = VisionAnalyzer()
    vector_store = VectorStore()
    graph_store = GraphStore()
    aligner = Aligner(graph_store=graph_store)

    graph_store.load()
    all_chunks = []

    # ---- Video ----
    if not args.skip_video:
        for video_path in raw["videos"]:
            with timer(f"Video extraction: {video_path.name}"):
                frames = video_extractor.extract(str(video_path))

            if not args.skip_vision:
                with timer(f"Vision analysis: {video_path.name}"):
                    frame_chunks = vision_analyzer.analyze_frames(frames)
                aligner.register_chunks(frame_chunks)
                all_chunks.extend(frame_chunks)

    # ---- Audio ----
    if not args.skip_audio:
        for video_path in raw["videos"]:
            with timer(f"Audio transcription: {video_path.name}"):
                segments = audio_extractor.extract_and_transcribe(str(video_path))
            audio_chunks = audio_segments_to_chunks(segments, str(video_path))
            aligner.register_chunks(audio_chunks)
            aligner.link_sequential(audio_chunks)
            all_chunks.extend(audio_chunks)

    # ---- PDFs ----
    for pdf_path in raw["pdfs"]:
        with timer(f"PDF extraction: {pdf_path.name}"):
            pages = doc_extractor.extract(str(pdf_path))
        pdf_chunks = pdf_pages_to_chunks(pages, str(pdf_path))
        aligner.register_chunks(pdf_chunks)
        aligner.link_sequential(pdf_chunks, relation="follows")
        all_chunks.extend(pdf_chunks)

        # Analyse embedded PDF images
        if not args.skip_vision:
            for page in pages:
                for img_path in page.image_paths:
                    try:
                        img_chunk = vision_analyzer.analyze_image(img_path, str(pdf_path))
                        aligner.register_chunks([img_chunk])
                        all_chunks.append(img_chunk)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Image analysis failed (%s): %s", img_path, exc)

    # ---- Standalone images ----
    if not args.skip_vision:
        for img_path in raw["images"]:
            with timer(f"Image analysis: {img_path.name}"):
                img_chunk = vision_analyzer.analyze_image(str(img_path))
            aligner.register_chunks([img_chunk])
            all_chunks.append(img_chunk)

    # ---- Embed & store ----
    if all_chunks:
        with timer("Vector store ingestion"):
            vector_store.add_chunks(all_chunks)
        logger.info("Stored %d chunks in vector store.", len(all_chunks))

    graph_store.save()
    logger.info(
        "Pipeline complete — graph: %d nodes, %d edges.",
        graph_store.node_count, graph_store.edge_count,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multimodal RAG Ingestion Pipeline")
    parser.add_argument("--skip-video", action="store_true", help="Skip video frame extraction")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio transcription")
    parser.add_argument("--skip-vision", action="store_true", help="Skip vision/image analysis")
    args = parser.parse_args()
    run_pipeline(args)
