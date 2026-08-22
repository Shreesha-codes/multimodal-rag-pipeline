"""
doc_extractor.py
----------------
Extracts text and embedded images from PDF documents using PyMuPDF (fitz).
Each page's text is preserved and images are saved to disk for vision analysis.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from src.models.schemas import PDFPage

logger = logging.getLogger(__name__)


class DocExtractor:
    """
    Parses PDF documents to extract:
    - Per-page text content
    - Embedded raster images (saved as PNG files)
    """

    def __init__(self, output_dir: str = "data/processed/pdf_images") -> None:
        """
        Parameters
        ----------
        output_dir : str
            Directory where extracted PDF images are saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, pdf_path: str) -> List[PDFPage]:
        """
        Extract text and images from every page of a PDF.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.

        Returns
        -------
        List[PDFPage]
            One PDFPage object per page, containing text and image paths.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info("Parsing PDF: %s", pdf_path.name)
        doc = fitz.open(str(pdf_path))
        pages: List[PDFPage] = []

        for page_num, page in enumerate(doc, start=1):
            # --- Text extraction ---
            text = page.get_text("text").strip()

            # --- Image extraction ---
            image_paths: List[str] = []
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list, start=1):
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image["image"]
                    img_ext = base_image["ext"]
                    img_filename = (
                        f"{pdf_path.stem}_p{page_num:03d}_img{img_index:02d}.{img_ext}"
                    )
                    img_path = self.output_dir / img_filename
                    img_path.write_bytes(img_bytes)
                    image_paths.append(str(img_path))
                    logger.debug("Saved image: %s", img_path.name)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Could not extract image %d on page %d: %s",
                        img_index, page_num, exc,
                    )

            pages.append(
                PDFPage(
                    source_pdf=str(pdf_path),
                    page_number=page_num,
                    text=text,
                    image_paths=image_paths,
                )
            )

        doc.close()
        logger.info(
            "PDF extraction complete — %d pages, %d images total.",
            len(pages),
            sum(len(p.image_paths) for p in pages),
        )
        return pages
