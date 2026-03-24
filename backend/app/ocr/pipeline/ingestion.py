from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os

import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image

from app.config import Settings

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def resolve_tesseract_cmd(cmd: str | None) -> str | None:
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


def is_pdf(filename: str | None, content_type: str | None) -> bool:
    filename = filename or ""
    return filename.lower().endswith(".pdf") or (content_type in PDF_CONTENT_TYPES)


def pil_to_ndarray(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def load_images(
    data: bytes,
    filename: str | None,
    content_type: str | None,
    settings: Settings,
) -> list[np.ndarray]:
    try:
        if is_pdf(filename, content_type):
            poppler_path = settings.poppler_path or None
            pil_pages = convert_from_bytes(data, fmt="jpeg", poppler_path=poppler_path)
            return [pil_to_ndarray(page) for page in pil_pages]

        with Image.open(BytesIO(data)) as image:
            return [pil_to_ndarray(image.convert("RGB"))]
    except Exception as e:
        raise ValueError(f"No se pudo procesar la imagen/PDF: {str(e)}")

