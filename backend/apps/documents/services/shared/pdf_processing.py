"""
PDF processing utilities.
Shared functions for PDF text extraction and image conversion.
"""

import logging
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str, max_pages: int = 2, max_chars: int = 3000) -> str:
    """
    Extract text from PDF using pdfplumber.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract
        max_chars: Maximum characters to return

    Returns:
        Extracted text string
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = []
            for page in pdf.pages[:max_pages]:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            return full_text[:max_chars]

    except Exception as e:
        logger.warning(f"PDF text extraction failed for {pdf_path}: {str(e)}")
        return ""


def convert_pdf_to_image(
    pdf_path: str,
    output_path: Optional[str] = None,
    page_number: int = 0,
    zoom: float = 2.0
) -> str:
    """
    Convert PDF page to image using PyMuPDF (cross-platform).

    Args:
        pdf_path: Path to PDF file
        output_path: Optional output path for image (auto-generated if None)
        page_number: Page number to convert (0-indexed)
        zoom: Zoom factor for image quality

    Returns:
        Path to generated image file

    Raises:
        RuntimeError: If PDF has no pages or conversion fails
    """
    pdf_path_obj = Path(pdf_path)

    if output_path is None:
        output_path = str(pdf_path_obj.parent / f"{pdf_path_obj.stem}_page{page_number}.png")

    try:
        with fitz.open(pdf_path) as pdf_document:
            if len(pdf_document) == 0:
                raise RuntimeError(f"PDF has no pages: {pdf_path}")

            if page_number >= len(pdf_document):
                raise RuntimeError(
                    f"Page {page_number} does not exist. PDF has {len(pdf_document)} pages."
                )

            # Get page and convert to image
            page = pdf_document[page_number]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            pix.save(output_path)

            logger.info(f"Converted PDF page {page_number} to image: {output_path}")
            return output_path

    except Exception as e:
        logger.exception(f"PDF to image conversion failed: {str(e)}")
        raise RuntimeError(f"Failed to convert PDF to image: {str(e)}")
