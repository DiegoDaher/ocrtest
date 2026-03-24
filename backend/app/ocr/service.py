from __future__ import annotations

from typing import Any

import pytesseract

from app.config import Settings
from app.models import DocumentType, OCRFields
from app.ocr import fields as field_extractors
from app.ocr.pipeline.ingestion import load_images, resolve_tesseract_cmd
from app.ocr.pipeline.orchestration import run_ocr_pipeline


def run_ocr(
    data: bytes,
    filename: str | None,
    content_type: str | None,
    document_type: DocumentType,
    settings: Settings,
) -> tuple[OCRFields, dict[str, Any]]:
    resolved_cmd = resolve_tesseract_cmd(settings.tesseract_cmd)
    if resolved_cmd:
        pytesseract.pytesseract.tesseract_cmd = resolved_cmd

    images = load_images(data, filename, content_type, settings)
    full_text, page_strategies = run_ocr_pipeline(images, document_type)

    parsed = field_extractors.extract_fields(full_text, document_type)
    parsed.full_text = full_text

    required_fields = (
        ("name", "clave", "certification_status")
        if document_type == DocumentType.CURP
        else ("name", "address", "curp", "birth_date", "validity")
    )
    missing_fields = [field_name for field_name in required_fields if not getattr(parsed, field_name)]

    metadata: dict[str, Any] = {
        "pages": len(images),
        "document_type": document_type.value,
        "ocr_strategy": page_strategies,
        "extraction_quality": {
            "missing_fields": missing_fields,
            "needs_review": bool(missing_fields),
        },
    }
    return parsed, metadata

