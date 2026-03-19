# Backend OCR API

API en FastAPI que procesa imágenes y PDFs de INE o CURP, ejecuta OCR (Tesseract) y extrae campos clave.

## Requisitos

- Python 3.11+
- Tesseract OCR instalado localmente
- Poppler (solo para PDFs)

## Configuración

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
copy .env.sample .env  # y ajustar rutas Tesseract/Poppler si aplica
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Endpoint principal: `POST /ocr` (form-data con `file` y campo query `document_type` = `ine` o `curp`).
