# Checklist de Modularizacion OCR Backend

Este checklist ayuda a extender el backend sin romper contratos publicos.

## Arquitectura interna vigente
- `app.ocr.service.run_ocr`: fachada interna consumida por la capa API.
- `app.ocr.pipeline.*`: pipeline OCR por responsabilidades.
- `app.ocr.extractors.*`: extraccion por tipo documental con registry.
- `app.ocr.fields.extract_fields`: fachada de compatibilidad.

## Checklist para agregar un nuevo documento
1. Agregar tipo en `app.models.DocumentType`.
2. Implementar extractor nuevo usando `app.ocr.extractors.template`.
3. Registrar extractor en `app.ocr.extractors.registry`.
4. Agregar pruebas de regresion con muestras representativas.
5. Verificar compatibilidad de `OCRFields` y `OCRResponse`.
6. Ejecutar `pytest` completo en backend.

## Reglas de seguridad funcional
- No romper `POST /ocr`.
- No renombrar ni eliminar campos de `OCRFields`.
- Mantener separacion entre OCR pipeline y reglas de extraccion.
