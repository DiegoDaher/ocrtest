from __future__ import annotations

from app.models import DocumentType, OCRFields
from app.ocr.extractors import registry


def test_registry_supports_current_document_types() -> None:
    supported = registry.get_supported_document_types()
    assert DocumentType.INE in supported
    assert DocumentType.CURP in supported


def test_registry_extract_fields_uses_resolved_extractor(monkeypatch) -> None:
    called: dict[str, str] = {}

    def fake_extractor(text: str) -> OCRFields:
        called["text"] = text
        return OCRFields(
            full_text=text,
            name="TEST USER",
            address=None,
            curp=None,
            clave=None,
            certification_status=None,
            is_certified=None,
            birth_date=None,
            validity=None,
        )

    monkeypatch.setattr(registry, "get_extractor", lambda document_type: fake_extractor)

    result = registry.extract_fields("dummy text", DocumentType.INE)

    assert called["text"] == "dummy text"
    assert result.name == "TEST USER"

