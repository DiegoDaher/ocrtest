from __future__ import annotations

from typing import Any

import numpy as np
import pytesseract

from app.models import DocumentType
from app.ocr.pipeline.preprocess import preprocess_variants
from app.ocr.pipeline.scoring import merge_top_texts, score_breakdown


def image_to_text(image: np.ndarray, document_type: DocumentType) -> tuple[str, str, list[dict[str, Any]]]:
    variants = preprocess_variants(image)
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

            breakdown = score_breakdown(text, document_type)
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
        merged_text = merge_top_texts(candidates)
        best_strategy = best["strategy"] if merged_text == best["text"] else f"{best['strategy']}+merge"
        return merged_text, best_strategy, candidates[:5]

    if errors:
        raise ValueError(f"Error en reconocimiento OCR: {errors[0]}")

    raise ValueError("No se detecto texto en la imagen")

