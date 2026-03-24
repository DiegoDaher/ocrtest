from __future__ import annotations

import re
from typing import Any

from app.models import DocumentType

COMMON_KEYWORDS = ("NOMBRE", "DOMICILIO", "CURP", "NACIMIENTO", "VIGENCIA", "VENCE")
INE_KEYWORDS = ("ELECTOR", "INSTITUTO", "CREDENCIAL")
CURP_KEYWORDS = ("REGISTRO", "POBLACION", "IDENTIDAD")


def score_breakdown(text: str, document_type: DocumentType) -> dict[str, int]:
    normalized = re.sub(r"\s+", " ", text.upper()).strip()
    if not normalized:
        return {
            "score": -10_000,
            "alnum_count": 0,
            "weird_count": 0,
            "token_count": 0,
            "keyword_hits": 0,
            "curp_hits": 0,
            "date_hits": 0,
        }

    alnum_count = sum(ch.isalnum() for ch in normalized)
    weird_count = sum(not (ch.isalnum() or ch.isspace() or ch in "/-.,:") for ch in normalized)
    token_count = len([t for t in normalized.split(" ") if len(t) > 1])

    score = alnum_count + (token_count * 2) - (weird_count * 2)
    keyword_hits = 0
    for keyword in COMMON_KEYWORDS:
        if keyword in normalized:
            score += 35
            keyword_hits += 1
    if document_type == DocumentType.INE:
        for keyword in INE_KEYWORDS:
            if keyword in normalized:
                score += 18
                keyword_hits += 1
    else:
        for keyword in CURP_KEYWORDS:
            if keyword in normalized:
                score += 18
                keyword_hits += 1

    curp_hits = 1 if re.search(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d", normalized) else 0
    if curp_hits:
        score += 80
    date_hits = 1 if re.search(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b", normalized) else 0
    if date_hits:
        score += 30

    return {
        "score": score,
        "alnum_count": alnum_count,
        "weird_count": weird_count,
        "token_count": token_count,
        "keyword_hits": keyword_hits,
        "curp_hits": curp_hits,
        "date_hits": date_hits,
    }


def line_fingerprint(line: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", line.upper())


def merge_top_texts(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return ""

    base = candidates[0]
    merged_blocks = [base["text"]]
    seen_lines = {line_fingerprint(line) for line in base["text"].splitlines() if line.strip()}

    for candidate in candidates[1:3]:
        if candidate["score"] < (base["score"] - 30):
            continue

        new_lines: list[str] = []
        for line in candidate["text"].splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            fingerprint = line_fingerprint(clean_line)
            if not fingerprint or fingerprint in seen_lines:
                continue
            new_lines.append(clean_line)
            seen_lines.add(fingerprint)

        if not new_lines:
            continue

        adds_signal = (
            candidate["curp_hits"] > base["curp_hits"]
            or candidate["date_hits"] > base["date_hits"]
            or candidate["keyword_hits"] > base["keyword_hits"]
        )
        if adds_signal or len(new_lines) >= 3:
            merged_blocks.append("\n".join(new_lines))

    return "\n".join(block for block in merged_blocks if block.strip()).strip()

