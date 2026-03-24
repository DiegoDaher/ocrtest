from __future__ import annotations

from app.models import OCRFields


class TemplateExtractor:
    """Reference template for new document extractors.

    Checklist:
    1) Implement extraction rules inside `extract`.
    2) Return `OCRFields` preserving expected base fields.
    3) Register extractor in `app.ocr.extractors.registry`.
    4) Add regression tests with representative OCR samples.
    """

    def extract(self, text: str) -> OCRFields:
        return OCRFields(
            full_text=text,
            name=None,
            address=None,
            curp=None,
            clave=None,
            certification_status=None,
            is_certified=None,
            birth_date=None,
            validity=None,
        )

