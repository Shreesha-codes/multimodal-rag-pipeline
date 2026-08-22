"""
helpers.py
----------
Shared utility functions used across the multimodal RAG pipeline.
Includes logging setup, file discovery, token estimation, and timing helpers.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
    fmt: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
) -> None:
    """
    Configure root logger with console (and optionally file) handlers.

    Parameters
    ----------
    level : int
        Logging level (e.g. logging.DEBUG, logging.INFO).
    log_file : str, optional
        If provided, logs are also written to this file path.
    fmt : str
        Log message format string.
    """
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
SUPPORTED_PDF_EXTS = {".pdf"}
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def discover_files(directory: str, extensions: set[str] | None = None) -> List[Path]:
    """
    Recursively discover files in a directory, filtered by extension.

    Parameters
    ----------
    directory : str
        Root directory to search.
    extensions : set[str], optional
        Set of lowercase extensions including dot (e.g. {'.pdf', '.mp4'}).
        If None, all files are returned.

    Returns
    -------
    List[Path]
        Sorted list of matching file paths.
    """
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    found: List[Path] = []
    for path in root.rglob("*"):
        if path.is_file():
            if extensions is None or path.suffix.lower() in extensions:
                found.append(path)

    return sorted(found)


def discover_raw_inputs(raw_dir: str = "data/raw") -> dict:
    """
    Scan the raw data directory and categorise files by type.

    Returns
    -------
    dict
        Keys: 'videos', 'pdfs', 'images' — each a list of Path objects.
    """
    return {
        "videos": discover_files(raw_dir, SUPPORTED_VIDEO_EXTS),
        "pdfs": discover_files(raw_dir, SUPPORTED_PDF_EXTS),
        "images": discover_files(raw_dir, SUPPORTED_IMAGE_EXTS),
    }


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """
    Rough token count estimation based on average characters per token.

    Parameters
    ----------
    text : str
        Input text.
    chars_per_token : float
        Characters per token (GPT-style ≈ 4, BPE ≈ 3.5–4).

    Returns
    -------
    int
        Estimated token count.
    """
    return max(1, int(len(text) / chars_per_token))


def truncate_to_token_limit(text: str, max_tokens: int = 4096) -> str:
    """
    Truncate text to approximately max_tokens tokens.

    Parameters
    ----------
    text : str
        Input text.
    max_tokens : int
        Maximum allowed token count.

    Returns
    -------
    str
        Possibly truncated text.
    """
    limit_chars = int(max_tokens * 4.0)
    if len(text) <= limit_chars:
        return text
    return text[:limit_chars] + "\n… [truncated]"


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

@contextmanager
def timer(label: str = "Operation") -> Generator[None, None, None]:
    """
    Context manager that logs the elapsed time for a block of code.

    Usage
    -----
    with timer("Ingestion"):
        run_ingestion()
    """
    logger = logging.getLogger(__name__)
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("%s completed in %.2fs", label, elapsed)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def ensure_dir(path: str) -> Path:
    """Create directory (and parents) if it doesn't exist, return Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_env(env_file: str = ".env") -> None:
    """Load environment variables from a .env file (python-dotenv)."""
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(env_file)
    except ImportError:
        logging.getLogger(__name__).warning(
            "python-dotenv not installed; skipping .env loading."
        )
