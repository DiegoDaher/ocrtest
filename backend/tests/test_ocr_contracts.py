from __future__ import annotations

from io import BytesIO

import numpy as np

from app.api.ocr_endpoint import process_ocr
from app.config import Settings
from app.models import DocumentType, OCRFields
from app.ocr import service


def _dummy_fields(full_text: str) -> OCRFields:
    return OCRFields(
        full_text=full_text,
        name="JUAN PEREZ",
        address="CALLE 1",
        curp="JUAP900101HDFXXX01",
        clave=None,
        certification_status=None,
        is_certified=None,
        birth_date="01/01/1990",
        validity="2030",
    )


def test_run_ocr_metadata_contains_critical_keys(monkeypatch) -> None:
    monkeypatch.setattr(service, "load_images", lambda data, filename, content_type, settings: [np.zeros((8, 8, 3), dtype=np.uint8)])
    monkeypatch.setattr(
        service,
        "run_ocr_pipeline",
        lambda images, document_type: (
            "NOMBRE JUAN PEREZ",
            [{"page": 1, "strategy": "gray|--oem 3 --psm 6", "candidates": []}],
        ),
    )
    monkeypatch.setattr(service.field_extractors, "extract_fields", lambda text, document_type: _dummy_fields(text))

    fields, metadata = service.run_ocr(
        data=b"fake",
        filename="sample.png",
        content_type="image/png",
        document_type=DocumentType.INE,
        settings=Settings(),
    )

    assert fields.name == "JUAN PEREZ"
    assert metadata["pages"] == 1
    assert metadata["document_type"] == "ine"
    assert "ocr_strategy" in metadata
    assert "extraction_quality" in metadata
    assert "missing_fields" in metadata["extraction_quality"]
    assert "needs_review" in metadata["extraction_quality"]


def test_ocr_endpoint_keeps_response_contract(monkeypatch) -> None:
    def fake_run_ocr(data, filename, content_type, document_type, settings):
        return _dummy_fields("texto de prueba"), {
            "pages": 1,
            "document_type": document_type.value,
            "ocr_strategy": [],
            "extraction_quality": {"missing_fields": [], "needs_review": False},
        }

    monkeypatch.setattr("app.api.ocr_endpoint.run_ocr", fake_run_ocr)

    class DummyUploadFile:
        def __init__(self, data: bytes, filename: str, content_type: str) -> None:
            self.file = BytesIO(data)
            self.filename = filename
            self.content_type = content_type

    response = process_ocr(
        document_type=DocumentType.INE,
        file=DummyUploadFile(data=b"1234", filename="sample.png", content_type="image/png"),
        settings=Settings(),
    )

    payload = response.model_dump()
    assert set(payload.keys()) == {"fields", "metadata"}
    assert set(payload["fields"].keys()) == {
        "full_text",
        "name",
        "address",
        "curp",
        "clave",
        "certification_status",
        "is_certified",
        "birth_date",
        "validity",
    }
    assert payload["metadata"]["document_type"] == "ine"
