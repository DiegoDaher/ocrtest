from __future__ import annotations

from app.models import DocumentType
from app.ocr.pipeline.scoring import merge_top_texts, score_breakdown


def test_score_breakdown_rewards_document_signal() -> None:
    signal_text = "NOMBRE JUAN PEREZ CURP JUAP900101HDFXXX01 INSTITUTO ELECTORAL VIGENCIA 2030"
    noise_text = "### ??? --"

    signal_score = score_breakdown(signal_text, DocumentType.INE)["score"]
    noise_score = score_breakdown(noise_text, DocumentType.INE)["score"]

    assert signal_score > noise_score


def test_merge_top_texts_adds_non_duplicated_lines_when_signal_improves() -> None:
    candidates = [
        {
            "text": "NOMBRE JUAN PEREZ\nCURP JUAP900101HDFXXX01",
            "score": 200,
            "keyword_hits": 1,
            "curp_hits": 1,
            "date_hits": 0,
        },
        {
            "text": "NOMBRE JUAN PEREZ\nVIGENCIA 2030",
            "score": 195,
            "keyword_hits": 2,
            "curp_hits": 1,
            "date_hits": 0,
        },
    ]

    merged = merge_top_texts(candidates)

    assert "NOMBRE JUAN PEREZ" in merged
    assert "CURP JUAP900101HDFXXX01" in merged
    assert "VIGENCIA 2030" in merged

