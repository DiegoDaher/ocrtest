from __future__ import annotations

from app.models import DocumentType, OCRFields
from app.ocr.extractors.registry import extract_fields as extract_fields_from_registry


def extract_fields(text: str, document_type: DocumentType) -> OCRFields:
    """Backward-compatible facade for field extraction."""
    return extract_fields_from_registry(text, document_type)

