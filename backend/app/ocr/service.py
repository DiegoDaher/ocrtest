from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os
from typing import Any

import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract

from app.config import Settings
from app.models import DocumentType, OCRFields
from app.ocr import fields as field_extractors

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def _resolve_tesseract_cmd(cmd: str | None) -> str | None:
    if not cmd:
        return None

    path = Path(cmd)
    if path.is_dir():
        exe_name = "tesseract.exe" if os.name == "nt" else "tesseract"
        candidate = path / exe_name
        if candidate.exists():
            return str(candidate)

    if path.exists():
        return str(path)

    return cmd


def _is_pdf(filename: str | None, content_type: str | None) -> bool:
    filename = filename or ""
    return filename.lower().endswith(".pdf") or (content_type in PDF_CONTENT_TYPES)


def _pil_to_ndarray(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _load_images(data: bytes, filename: str | None, content_type: str | None, settings: Settings) -> list[np.ndarray]:
    try:
        if _is_pdf(filename, content_type):
            poppler_path = settings.poppler_path or None
            pil_pages = convert_from_bytes(data, fmt="jpeg", poppler_path=poppler_path)
            return [_pil_to_ndarray(page) for page in pil_pages]

        with Image.open(BytesIO(data)) as image:
            return [_pil_to_ndarray(image.convert("RGB"))]
    except Exception as e:
        raise ValueError(f"No se pudo procesar la imagen/PDF: {str(e)}")


def _preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 45, 11)
    return thresh


def _image_to_text(image: np.ndarray) -> str:
    try:
        config = "--oem 3 --psm 6"
        return pytesseract.image_to_string(image, config=config, lang="spa")
    except Exception as e:
        raise ValueError(f"Error en reconocimiento OCR: {str(e)}")


def run_ocr(
    data: bytes,
    filename: str | None,
    content_type: str | None,
    document_type: DocumentType,
    settings: Settings,
) -> tuple[OCRFields, dict[str, Any]]:
    resolved_cmd = _resolve_tesseract_cmd(settings.tesseract_cmd)
    if resolved_cmd:
        pytesseract.pytesseract.tesseract_cmd = resolved_cmd

    images = _load_images(data, filename, content_type, settings)
    texts: list[str] = []
    for image in images:
        processed = _preprocess(image)
        texts.append(_image_to_text(processed))

    full_text = "\n".join(texts)
    parsed = field_extractors.extract_fields(full_text, document_type)
    parsed.full_text = full_text

    metadata: dict[str, Any] = {
        "pages": len(images),
        "document_type": document_type.value,
    }
    return parsed, metadata
