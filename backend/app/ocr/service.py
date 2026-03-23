from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os
import re
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
COMMON_KEYWORDS = ("NOMBRE", "DOMICILIO", "CURP", "NACIMIENTO", "VIGENCIA", "VENCE")
INE_KEYWORDS = ("ELECTOR", "INSTITUTO", "CREDENCIAL")
CURP_KEYWORDS = ("REGISTRO", "POBLACION", "IDENTIDAD")


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


def _detect_document_regions(
    image: np.ndarray,
    min_area_ratio: float = 0.008,
    max_regions: int = 3,
    margin: int = 24,
) -> list[tuple[str, np.ndarray]]:
    height, width = image.shape[:2]
    page_area = float(height * width)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect non-white content blocks (typical when cards are centered on a white PDF page).
    _, mask = cv2.threshold(gray, 242, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((15, 15), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: list[tuple[int, int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < int(page_area * min_area_ratio):
            continue
        boxes.append((x, y, w, h, area))

    if not boxes:
        return [("full", image)]

    boxes.sort(key=lambda item: item[4], reverse=True)
    regions: list[tuple[str, np.ndarray]] = []
    for idx, (x, y, w, h, _) in enumerate(boxes[:max_regions], start=1):
        x0 = max(0, x - margin)
        y0 = max(0, y - margin)
        x1 = min(width, x + w + margin)
        y1 = min(height, y + h + margin)
        crop = image[y0:y1, x0:x1]
        if crop.size == 0:
            continue
        regions.append((f"region_{idx}", crop))

    return regions or [("full", image)]


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


def _resize_for_ocr(gray: np.ndarray, min_width: int = 1800) -> np.ndarray:
    height, width = gray.shape[:2]
    if width >= min_width:
        return gray

    scale = min_width / float(width)
    resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return resized


def _deskew(gray: np.ndarray) -> np.ndarray:
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    points = np.column_stack(np.where(threshold > 0))
    if points.size == 0:
        return gray

    angle = cv2.minAreaRect(points)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.3:
        return gray

    height, width = gray.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        gray,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _preprocess_variants(image: np.ndarray) -> dict[str, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = _resize_for_ocr(gray)
    contrast = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(resized)
    denoised = cv2.bilateralFilter(contrast, d=9, sigmaColor=75, sigmaSpace=75)
    deskewed = _deskew(denoised)
    blur = cv2.GaussianBlur(deskewed, (3, 3), 0)

    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        15,
    )
    inverted = cv2.bitwise_not(otsu)

    variants: dict[str, np.ndarray] = {
        "gray": blur,
        "otsu": otsu,
        "adaptive": adaptive,
        "inverted": inverted,
    }

    # Card-focused variants: for INE-like crops, boost lower/detail area where CURP and address are usually printed.
    height, width = image.shape[:2]
    aspect_ratio = (width / float(height)) if height else 0.0
    if 1.2 <= aspect_ratio <= 2.2 and width >= 350 and height >= 220:
        y0 = int(height * 0.18)
        y1 = int(height * 0.95)
        x0 = int(width * 0.08)
        x1 = int(width * 0.95)
        focus = image[y0:y1, x0:x1]
        if focus.size > 0:
            focus_gray = cv2.cvtColor(focus, cv2.COLOR_BGR2GRAY)
            for scale in (2.0, 3.0):
                upscaled = cv2.resize(focus_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                clahe_focus = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(upscaled)
                _, otsu_focus = cv2.threshold(clahe_focus, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                variants[f"focus_clahe_x{int(scale * 10)}"] = clahe_focus
                variants[f"focus_otsu_x{int(scale * 10)}"] = otsu_focus

    return variants


def _score_breakdown(text: str, document_type: DocumentType) -> dict[str, int]:
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


def _line_fingerprint(line: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", line.upper())


def _merge_top_texts(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return ""

    base = candidates[0]
    merged_blocks = [base["text"]]
    seen_lines = {_line_fingerprint(line) for line in base["text"].splitlines() if line.strip()}

    for candidate in candidates[1:3]:
        if candidate["score"] < (base["score"] - 30):
            continue

        new_lines: list[str] = []
        for line in candidate["text"].splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            fingerprint = _line_fingerprint(clean_line)
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


def _image_to_text(image: np.ndarray, document_type: DocumentType) -> tuple[str, str, list[dict[str, Any]]]:
    variants = _preprocess_variants(image)
    base_configs = ("--oem 3 --psm 6", "--oem 3 --psm 11", "--oem 3 --psm 4")
    focus_configs = ("--oem 3 --psm 11", "--oem 3 --psm 6")

    candidates: list[dict[str, Any]] = []
    errors: list[str] = []

    for variant_name, variant in variants.items():
        configs = focus_configs if variant_name.startswith("focus_") else base_configs
        for config in configs:
            strategy = f"{variant_name}|{config}"
            try:
                text = pytesseract.image_to_string(variant, config=config, lang="spa+eng")
            except Exception as e:
                errors.append(f"{strategy}: {str(e)}")
                continue

            text = text.strip()
            if not text:
                continue

            breakdown = _score_breakdown(text, document_type)
            candidates.append(
                {
                    "strategy": strategy,
                    "text": text,
                    "score": breakdown["score"],
                    "char_count": len(text),
                    "token_count": breakdown["token_count"],
                    "keyword_hits": breakdown["keyword_hits"],
                    "curp_hits": breakdown["curp_hits"],
                    "date_hits": breakdown["date_hits"],
                }
            )

    if candidates:
        candidates.sort(key=lambda item: item["score"], reverse=True)
        best = candidates[0]
        merged_text = _merge_top_texts(candidates)
        best_strategy = best["strategy"] if merged_text == best["text"] else f"{best['strategy']}+merge"
        return merged_text, best_strategy, candidates[:5]

    if errors:
        raise ValueError(f"Error en reconocimiento OCR: {errors[0]}")

    raise ValueError("No se detecto texto en la imagen")


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
    page_strategies: list[dict[str, Any]] = []
    for page_index, image in enumerate(images, start=1):
        region_results: list[dict[str, Any]] = []
        regions = _detect_document_regions(image)

        for region_name, region_image in regions:
            try:
                region_text, strategy, candidates = _image_to_text(region_image, document_type)
            except ValueError:
                continue
            region_results.append(
                {
                    "region": region_name,
                    "text": region_text,
                    "strategy": strategy,
                    "best_score": candidates[0]["score"] if candidates else -10_000,
                    "best_keyword_hits": candidates[0]["keyword_hits"] if candidates else 0,
                    "best_curp_hits": candidates[0]["curp_hits"] if candidates else 0,
                    "best_date_hits": candidates[0]["date_hits"] if candidates else 0,
                    "candidates": candidates,
                }
            )

        if not region_results:
            page_text, strategy, candidates = _image_to_text(image, document_type)
            region_results = [
                {
                    "region": "full",
                    "text": page_text,
                    "strategy": strategy,
                    "best_score": candidates[0]["score"] if candidates else -10_000,
                    "best_keyword_hits": candidates[0]["keyword_hits"] if candidates else 0,
                    "best_curp_hits": candidates[0]["curp_hits"] if candidates else 0,
                    "best_date_hits": candidates[0]["date_hits"] if candidates else 0,
                    "candidates": candidates,
                }
            ]

        region_results.sort(key=lambda item: item["best_score"], reverse=True)
        selected_texts: list[str] = []
        selected_region_names: list[str] = []
        if region_results:
            selected_texts.append(region_results[0]["text"])
            selected_region_names.append(region_results[0]["region"])
            for region_result in region_results[1:]:
                has_signal = (
                    region_result["best_keyword_hits"] > 0
                    or region_result["best_curp_hits"] > 0
                    or region_result["best_date_hits"] > 0
                    or "<<" in region_result["text"]
                    or "IDMEX" in region_result["text"].upper()
                )
                if has_signal:
                    selected_texts.append(region_result["text"])
                    selected_region_names.append(region_result["region"])

        page_text = "\n".join(selected_texts).strip() if selected_texts else region_results[0]["text"]
        texts.append(page_text)

        best_region = region_results[0]
        page_strategies.append(
            {
                "page": page_index,
                "regions_detected": len(regions),
                "regions_ocr": len(region_results),
                "selected_regions": selected_region_names or [best_region["region"]],
                "strategy": best_region["strategy"],
                "candidates": [
                    {
                        "region": best_region["region"],
                        "strategy": candidate["strategy"],
                        "score": candidate["score"],
                        "char_count": candidate["char_count"],
                        "token_count": candidate["token_count"],
                        "keyword_hits": candidate["keyword_hits"],
                        "curp_hits": candidate["curp_hits"],
                        "date_hits": candidate["date_hits"],
                        "preview": candidate["text"][:120],
                    }
                    for candidate in best_region["candidates"]
                ],
            }
        )

    full_text = "\n".join(texts)
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
