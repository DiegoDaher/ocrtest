from __future__ import annotations

from typing import Any

import numpy as np

from app.models import DocumentType
from app.ocr.pipeline.preprocess import detect_document_regions
from app.ocr.pipeline.recognition import image_to_text


def run_ocr_pipeline(images: list[np.ndarray], document_type: DocumentType) -> tuple[str, list[dict[str, Any]]]:
    texts: list[str] = []
    page_strategies: list[dict[str, Any]] = []
    for page_index, image in enumerate(images, start=1):
        region_results: list[dict[str, Any]] = []
        regions = detect_document_regions(image)

        for region_name, region_image in regions:
            try:
                region_text, strategy, candidates = image_to_text(region_image, document_type)
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
            page_text, strategy, candidates = image_to_text(image, document_type)
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
    return full_text, page_strategies

