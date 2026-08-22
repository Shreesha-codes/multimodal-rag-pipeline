"""
audio_extractor.py
------------------
Extracts audio from a video file and transcribes it using OpenAI Whisper.
Produces a list of AudioSegment objects with timestamps and transcript text.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

from src.models.schemas import AudioSegment

logger = logging.getLogger(__name__)


class AudioExtractor:
    """
    Extracts audio track from a video/audio file and transcribes it
    using the Whisper ASR model.
    """

    def __init__(
        self,
        output_dir: str = "data/processed/audio",
        whisper_model: str = "base",
        language: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        output_dir : str
            Directory where extracted .wav files will be saved.
        whisper_model : str
            Whisper model size: 'tiny', 'base', 'small', 'medium', 'large'.
        language : str, optional
            Language hint for transcription (e.g. 'en'). None = auto-detect.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model_name = whisper_model
        self.language = language
        self._model = None  # lazy-loaded

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_model(self):
        """Lazy-load Whisper model on first use."""
        if self._model is None:
            import whisper  # type: ignore
            logger.info("Loading Whisper model '%s'…", self.whisper_model_name)
            self._model = whisper.load_model(self.whisper_model_name)
        return self._model

    def _extract_audio(self, video_path: Path) -> Path:
        """Extract audio track from a video and return path to .wav file."""
        from moviepy.editor import VideoFileClip  # type: ignore

        audio_path = self.output_dir / f"{video_path.stem}.wav"
        if audio_path.exists():
            logger.info("Audio already extracted: %s", audio_path)
            return audio_path

        logger.info("Extracting audio from '%s'…", video_path.name)
        clip = VideoFileClip(str(video_path))
        clip.audio.write_audiofile(str(audio_path), logger=None)
        clip.close()
        logger.info("Audio saved to: %s", audio_path)
        return audio_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_and_transcribe(self, source_path: str) -> List[AudioSegment]:
        """
        Extract audio (if video) and transcribe it with Whisper.

        Parameters
        ----------
        source_path : str
            Path to a .mp4, .mov, .avi, or .wav/.mp3 file.

        Returns
        -------
        List[AudioSegment]
            Time-stamped transcript segments.
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        # If it's a video, extract audio first
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        if source.suffix.lower() in video_exts:
            audio_path = self._extract_audio(source)
        else:
            audio_path = source

        model = self._load_model()
        logger.info("Transcribing '%s'…", audio_path.name)

        result = model.transcribe(
            str(audio_path),
            language=self.language,
            verbose=False,
        )

        segments: List[AudioSegment] = []
        for seg in result.get("segments", []):
            segments.append(
                AudioSegment(
                    source_audio=str(audio_path),
                    start_sec=round(seg["start"], 3),
                    end_sec=round(seg["end"], 3),
                    transcript=seg["text"].strip(),
                )
            )

        logger.info("Transcription complete — %d segments produced.", len(segments))
        return segments
