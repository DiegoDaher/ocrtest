from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from app.models import DocumentType, OCRFields

CURP_REGEX = re.compile(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d")
DATE_REGEX = re.compile(r"\b(\d{2}[\/-]\d{2}[\/-]\d{4})\b")
VALIDITY_REGEX = re.compile(r"\b(\d{2}[\/-]\d{2}[\/-]\d{4}|\d{4})\b")


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.upper())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _line_iter(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _value_after_keywords(lines: Iterable[str], keywords: tuple[str, ...]) -> str | None:
    for line in lines:
        for keyword in keywords:
            if keyword in line:
                parts = line.split(keyword, maxsplit=1)
                candidate = parts[1].strip(" :.-") if len(parts) > 1 else ""
                if candidate:
                    return candidate
    # If not found inline, try next non-empty line after keyword
    lines_list = list(lines)
    for idx, line in enumerate(lines_list):
        for keyword in keywords:
            if keyword in line and idx + 1 < len(lines_list):
                return lines_list[idx + 1]
    return None


def _extract_curp(text: str) -> str | None:
    match = CURP_REGEX.search(text)
    return match.group(0) if match else None


def _extract_birth_date(text: str) -> str | None:
    match = DATE_REGEX.search(text)
    return match.group(1) if match else None


def _extract_validity(lines: list[str]) -> str | None:
    for line in lines:
        if "VIGENCIA" in line or "VENCE" in line:
            match = VALIDITY_REGEX.search(line)
            if match:
                return match.group(1)
    return None


def extract_fields(text: str, document_type: DocumentType) -> OCRFields:
    normalized_text = _normalize(text)
    lines = _line_iter(normalized_text)

    name = None
    address = None
    birth_date = _extract_birth_date(normalized_text)
    validity = _extract_validity(lines)
    curp = _extract_curp(normalized_text)

    if document_type == DocumentType.INE:
        name = _value_after_keywords(lines, ("NOMBRE", "NOMBRES"))
        address = _value_after_keywords(lines, ("DOMICILIO", "DIRECCION"))
    elif document_type == DocumentType.CURP:
        name = _value_after_keywords(lines, ("NOMBRE", "NOMBRES"))
        address = _value_after_keywords(lines, ("DOMICILIO", "ENTIDAD"))
        if not curp:
            curp = _value_after_keywords(lines, ("CURP",))

    return OCRFields(
        full_text=text,
        name=name,
        address=address,
        curp=curp,
        birth_date=birth_date,
        validity=validity,
    )
