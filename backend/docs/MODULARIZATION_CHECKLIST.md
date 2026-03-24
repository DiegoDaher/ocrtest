# OCR Backend Modularization

This document describes how to add new document extractors without changing
public API contracts.

## Current Internal Architecture

- `app.ocr.service.run_ocr`: public internal facade used by API layer.
- `app.ocr.pipeline.*`: OCR processing split by responsibilities.
- `app.ocr.extractors.*`: field extraction by document type with registry.
- `app.ocr.fields.extract_fields`: backward-compatible facade for extractor dispatch.

## Checklist: Add New Document Type

1. Add the new enum value in `app.models.DocumentType`.
2. Implement extractor class using the template in `app.ocr.extractors.template`.
3. Register extractor in `app.ocr.extractors.registry`.
4. Add regression tests with representative OCR text samples.
5. Verify metadata and response contract remain compatible.
6. Run full backend tests (`pytest`) before merging.

## Notes

- Keep `OCRFields` and `OCRResponse` stable unless explicitly planned.
- Prefer new extractor modules over expanding large conditional blocks.
- Keep OCR pipeline changes isolated from extraction rules whenever possible.

