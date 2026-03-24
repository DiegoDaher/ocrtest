# Quick Start - Backend OCR (Windows-First)

## 1. Instalacion rapida
Desde `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crear `backend/.env` con rutas locales:

```env
TESSERACT_CMD=C:\ruta\a\tesseract.exe
TESSDATA_PREFIX=C:\ruta\a\tesseract\tessdata
POPPLER_PATH=C:\ruta\a\poppler\Library\bin
```

Levantar API:

```powershell
uvicorn app.main:app --reload
```

## 2. Prueba rapida
Health:

```bash
curl http://localhost:8000/health
```

OCR:

```bash
curl -X POST "http://localhost:8000/ocr?document_type=ine" -F "file=@./archivo.pdf"
```

## 3. Documentacion principal
Este archivo es indice de navegacion.

- Guia tecnica completa:
- `backend/docs/SERVICE_BACKEND_GUIDE.md`

- Referencia API y consumo (incluye frontend como cliente):
- `backend/docs/API_REFERENCE_AND_CONSUMPTION.md`

- Guia para extender extraccion por reglas/extractores:
- `backend/docs/EXTRACTION_EXTENSION_GUIDE.md`

- Roadmap ejecutable de integracion ML hibrida:
- `backend/docs/ML_HYBRID_IMPLEMENTATION_ROADMAP.md`

- Checklist de modularizacion:
- `backend/docs/MODULARIZATION_CHECKLIST.md`

## 4. Notas de compatibilidad
Contrato publico estable (sin cambios):
- `POST /ocr`
- `DocumentType` (`ine`, `curp`)
- `OCRFields`
- `OCRResponse`
