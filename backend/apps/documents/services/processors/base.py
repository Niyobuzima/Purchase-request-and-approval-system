"""
Base utilities for document processing.
Shared functions and OpenAI client management.
"""

import os
import base64
import logging
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber
from openai import OpenAI

logger = logging.getLogger(__name__)

# OpenAI client - initialized lazily
_openai_client = None


def get_openai_client() -> OpenAI:
    """
    Get or create OpenAI client instance.
    Uses lazy initialization to avoid requiring API key at import time.
    """
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it before using document processing features."
            )
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def encode_image(image_path: str) -> str:
    """Encode image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_mime_type(file_path: str) -> str:
    """Get MIME type from file extension."""
    file_ext = Path(file_path).suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp'
    }
    return mime_types.get(file_ext, 'image/jpeg')


def pdf_to_image(pdf_path: str, output_path: str | None = None) -> str:
    """
    Convert first page of PDF to image using PyMuPDF.
    Cross-platform, no external dependencies.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Optional output path for image (default: replaces .pdf with .png)
    
    Returns:
        Path to generated image
    """
    if output_path is None:
        output_path = pdf_path.replace('.pdf', '_temp.png')
    
    try:
        pdf_document = fitz.open(pdf_path)
        
        if len(pdf_document) == 0:
            raise RuntimeError("PDF has no pages")
        
        # Get first page
        first_page = pdf_document[0]
        
        # Render to image at 144 DPI (zoom=2.0 for good quality)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = first_page.get_pixmap(matrix=mat)
        
        # Save as PNG
        pix.save(output_path)
        
        # Close PDF
        pdf_document.close()
        
        logger.info(f"Converted PDF to image: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {str(e)}")
        raise RuntimeError(f"Failed to convert PDF to image: {str(e)}")


def extract_text_from_pdf(pdf_path: str, max_pages: int = 3, max_chars: int = 4000) -> str:
    """
    Extract text from PDF using pdfplumber.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract (default: 3)
        max_chars: Maximum characters to return (default: 4000)
    
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
        logger.warning(f"Text extraction failed: {str(e)}")
        return ""


def call_gpt_vision(
    image_path: str,
    prompt: str,
    model: str = "gpt-5",
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> str:
    """
    Call OpenAI GPT Vision API with an image.
    
    Args:
        image_path: Path to image file
        prompt: Text prompt for the model
        model: Model to use (default: gpt-5)
        temperature: Sampling temperature
        max_tokens: Maximum output tokens
    
    Returns:
        Raw JSON string from API response
    """
    base64_image = encode_image(image_path)
    mime_type = get_mime_type(image_path)
    
    try:
        response = get_openai_client().responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:{mime_type};base64,{base64_image}"}
                    ]
                }
            ],
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        # Extract JSON from Response API
        raw_json = None
        if hasattr(response, "output_text") and response.output_text:
            raw_json = response.output_text
        elif hasattr(response, "output"):
            try:
                raw_json = response.output[0].content[0].text
            except Exception:
                pass
        if raw_json is None and hasattr(response, "choices"):
            try:
                raw_json = response.choices[0].message.content
            except Exception:
                pass
        
        if not raw_json:
            raise RuntimeError("OpenAI Response API did not contain expected text output")
        
        logger.info("Successfully received response from OpenAI Response API")
        return raw_json
        
    except Exception as e:
        logger.error(f"GPT Vision API call failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"GPT Vision API call failed: {str(e)}")
