"""
SentinelAI — Preprocessing Utilities

Common preprocessing functions for text and image inputs.
"""

import hashlib
import re
import string
from typing import Optional


def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hash of content for audit deduplication."""
    return hashlib.sha256(content).hexdigest()


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of text content."""
    return compute_hash(text.encode("utf-8"))


def clean_text(text: str) -> str:
    """
    Basic text cleaning:
    - Collapse whitespace
    - Strip leading/trailing spaces
    - Remove null bytes
    """
    text = text.replace("\x00", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract readable text from a PDF file.
    
    Uses PyPDF2 for text extraction.
    Falls back to empty string on failure.
    """
    try:
        import io
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
        
        return "\n\n".join(pages_text)
    except Exception as e:
        return ""


def truncate_text(text: str, max_length: int = 10000) -> str:
    """Truncate text to a maximum character length for processing."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def validate_image_format(content_type: Optional[str]) -> bool:
    """Check that the uploaded file is a supported image format."""
    supported = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
    return content_type in supported if content_type else False


def validate_pdf(content_type: Optional[str]) -> bool:
    """Check that the uploaded file is a PDF."""
    return content_type == "application/pdf" if content_type else False
