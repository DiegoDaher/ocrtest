from __future__ import annotations

from typing import Callable

from app.models import DocumentType, OCRFields
from app.ocr.extractors.curp import CURPExtractor
from app.ocr.extractors.ine import INEExtractor

ExtractorFn = Callable[[str], OCRFields]


class ExtractorRegistry:
    def __init__(self) -> None:
        self._extractors: dict[DocumentType, ExtractorFn] = {}

    def register(self, document_type: DocumentType, extractor: ExtractorFn) -> None:
        self._extractors[document_type] = extractor

    def get(self, document_type: DocumentType) -> ExtractorFn:
        try:
            return self._extractors[document_type]
        except KeyError as exc:
            raise ValueError(f"No hay extractor registrado para {document_type.value}") from exc

    def supported_types(self) -> set[DocumentType]:
        return set(self._extractors.keys())


def _build_default_registry() -> ExtractorRegistry:
    registry = ExtractorRegistry()
    registry.register(DocumentType.INE, INEExtractor().extract)
    registry.register(DocumentType.CURP, CURPExtractor().extract)
    return registry


_DEFAULT_REGISTRY = _build_default_registry()


def register_extractor(document_type: DocumentType, extractor: ExtractorFn) -> None:
    _DEFAULT_REGISTRY.register(document_type, extractor)


def get_extractor(document_type: DocumentType) -> ExtractorFn:
    return _DEFAULT_REGISTRY.get(document_type)


def get_supported_document_types() -> set[DocumentType]:
    return _DEFAULT_REGISTRY.supported_types()


def extract_fields(text: str, document_type: DocumentType) -> OCRFields:
    extractor = get_extractor(document_type)
    return extractor(text)

