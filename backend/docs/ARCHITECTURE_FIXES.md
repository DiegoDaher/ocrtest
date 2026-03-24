# Architecture Status and Fixes (Actualizado)

## 1. Estado actual
La arquitectura backend esta modularizada y operativa.

Capas activas:
- API: `app/main.py` + `app/api/ocr_endpoint.py`
- Servicio OCR: `app/ocr/service.py`
- Pipeline OCR: `app/ocr/pipeline/*`
- Extraccion documental: `app/ocr/extractors/*`

## 2. Contrato publico (estable)
Sin cambios en interfaces publicas:
- Endpoint `POST /ocr`
- `DocumentType`: `ine`, `curp`
- `OCRFields`
- `OCRResponse`

## 3. Fixes relevantes vigentes
- CORS abierto para entorno local (origins `*`, sin credenciales).
- Validacion de archivo en endpoint (`nombre`, `contenido`, `tamano <= 10MB`).
- Mapeo de errores:
- `ValueError` -> HTTP 400
- error inesperado -> HTTP 500
- Metadatos de calidad en cada respuesta (`missing_fields`, `needs_review`).

## 4. Flujo resumido
```text
/ocr request
  -> validaciones endpoint
  -> run_ocr
  -> ingestion + preprocess + recognition + scoring + orchestration
  -> extractor por tipo documental
  -> OCRResponse(fields, metadata)
```

## 5. Riesgos conocidos y mitigaciones
Riesgo | Mitigacion actual
- Calidad OCR variable | multiples estrategias y scoring por senal
- Campos faltantes | `extraction_quality.needs_review`
- Dependencia de Tesseract/Poppler | configuracion env + troubleshooting
- Regresiones por reglas nuevas | tests de regresion por extractor

## 6. Evolucion recomendada
- Mantener reglas como baseline productivo.
- Integrar ML hibrido por fases (shadow -> canary -> rollout).
- No romper payload actual.

## 7. Referencias
- `backend/docs/SERVICE_BACKEND_GUIDE.md`
- `backend/docs/API_REFERENCE_AND_CONSUMPTION.md`
- `backend/docs/ML_HYBRID_IMPLEMENTATION_ROADMAP.md`
