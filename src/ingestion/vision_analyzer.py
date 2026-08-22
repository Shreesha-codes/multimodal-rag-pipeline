"""
vision_analyzer.py
------------------
Generates natural-language descriptions for images and video frames
using a multimodal LLM (Google Gemini Vision).
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import List, Optional

from src.models.schemas import Chunk, ChunkType, ModalityType, VideoFrame

logger = logging.getLogger(__name__)

# Default prompt used when no custom prompt is supplied
DEFAULT_PROMPT = (
    "Describe this image in detail. Focus on: key objects, text visible, "
    "diagrams or charts, spatial layout, and any notable information that "
    "would be useful for answering questions about the content."
)


class VisionAnalyzer:
    """
    Sends images to a multimodal LLM and returns descriptive text chunks
    suitable for embedding and retrieval.
    """

    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        prompt: str = DEFAULT_PROMPT,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        model_name : str
            Gemini model identifier (e.g. 'gemini-1.5-flash', 'gemini-1.5-pro').
        prompt : str
            System prompt sent alongside each image.
        api_key : str, optional
            Google AI API key. Falls back to GOOGLE_API_KEY env variable.
        """
        self.model_name = model_name
        self.prompt = prompt
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._client = None  # lazy-loaded

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Lazy-initialise the Gemini client."""
        if self._client is None:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model_name)
        return self._client

    @staticmethod
    def _encode_image(image_path: Path) -> dict:
        """Return an inline_data part dict for the Gemini API."""
        suffix = image_path.suffix.lower().lstrip(".")
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
        mime_type = mime_map.get(suffix, "image/jpeg")
        data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return {"inline_data": {"mime_type": mime_type, "data": data}}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_image(self, image_path: str, source_file: Optional[str] = None) -> Chunk:
        """
        Describe a single image file.

        Parameters
        ----------
        image_path : str
            Path to the image file.
        source_file : str, optional
            Logical source name to tag in the returned chunk.

        Returns
        -------
        Chunk
            A text chunk containing the image description.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        client = self._get_client()
        image_part = self._encode_image(path)

        response = client.generate_content([self.prompt, image_part])
        description = response.text.strip()

        return Chunk(
            source_file=source_file or str(path),
            modality=ModalityType.IMAGE,
            chunk_type=ChunkType.IMAGE_DESCRIPTION,
            content=description,
            metadata={"image_path": str(path)},
        )

    def analyze_frames(self, frames: List[VideoFrame]) -> List[Chunk]:
        """
        Describe a list of video frames.

        Parameters
        ----------
        frames : List[VideoFrame]
            Frame metadata objects produced by VideoExtractor.

        Returns
        -------
        List[Chunk]
            One descriptive Chunk per frame.
        """
        chunks: List[Chunk] = []
        for i, frame in enumerate(frames, start=1):
            logger.info(
                "Analyzing frame %d/%d (t=%.2fs)…", i, len(frames), frame.timestamp_sec
            )
            try:
                path = Path(frame.frame_path)
                client = self._get_client()
                image_part = self._encode_image(path)
                response = client.generate_content([self.prompt, image_part])
                description = response.text.strip()

                # Update the frame object with description
                frame.description = description

                chunks.append(
                    Chunk(
                        source_file=frame.source_video,
                        modality=ModalityType.VIDEO,
                        chunk_type=ChunkType.FRAME_DESCRIPTION,
                        content=description,
                        metadata={
                            "frame_path": str(frame.frame_path),
                            "timestamp_sec": frame.timestamp_sec,
                            "frame_id": frame.frame_id,
                        },
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Frame %d analysis failed: %s", i, exc)

        logger.info("Vision analysis complete — %d chunks produced.", len(chunks))
        return chunks
