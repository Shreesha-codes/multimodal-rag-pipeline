"""
video_extractor.py
------------------
Extracts frames from a video file at configurable intervals.
Uses OpenCV (cv2) to decode and save individual frames as images.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import List

import cv2

from src.models.schemas import VideoFrame

logger = logging.getLogger(__name__)


class VideoExtractor:
    """
    Extracts frames from a video file at a given FPS rate and
    saves them to the output directory.
    """

    def __init__(
        self,
        output_dir: str = "data/processed/frames",
        frame_rate: float = 1.0,
        image_format: str = "jpg",
    ) -> None:
        """
        Parameters
        ----------
        output_dir : str
            Directory where extracted frames will be saved.
        frame_rate : float
            How many frames to extract per second of video (default: 1 fps).
        image_format : str
            Output image format, e.g. 'jpg' or 'png'.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.frame_rate = frame_rate
        self.image_format = image_format

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, video_path: str) -> List[VideoFrame]:
        """
        Extract frames from a video file.

        Parameters
        ----------
        video_path : str
            Path to the input video file.

        Returns
        -------
        List[VideoFrame]
            Metadata objects for each extracted frame.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info("Opening video: %s", video_path)
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps
        interval = int(fps / self.frame_rate) if self.frame_rate > 0 else int(fps)

        logger.info(
            "Video info — FPS: %.2f | Total frames: %d | Duration: %.1fs | Interval: %d",
            fps, total_frames, duration_sec, interval,
        )

        frames: List[VideoFrame] = []
        frame_index = 0
        saved_count = 0
        stem = video_path.stem

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % interval == 0:
                timestamp = frame_index / fps
                filename = f"{stem}_frame_{saved_count:05d}_{timestamp:.2f}s.{self.image_format}"
                frame_path = self.output_dir / filename
                cv2.imwrite(str(frame_path), frame)

                frames.append(
                    VideoFrame(
                        source_video=str(video_path),
                        timestamp_sec=round(timestamp, 3),
                        frame_path=str(frame_path),
                    )
                )
                saved_count += 1

            frame_index += 1

        cap.release()
        logger.info("Extracted %d frames from '%s'", saved_count, video_path.name)
        return frames
