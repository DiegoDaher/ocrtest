# OCR Demo (FastAPI + Next.js)

Proyecto de ejemplo para extraer campos clave (Nombre, Domicilio, CURP, Fecha de nacimiento y Vigencia) desde PDFs/imagenes de credenciales INE o constancias CURP.

## Backend (FastAPI)

Ubicación: `backend/`

1. Crear entorno virtual y dependencias:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.sample .env    # Ajusta rutas Tesseract/Poppler
   ```
2. Requisitos externos: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) y [Poppler](https://poppler.freedesktop.org/) (para PDFs).
3. Ejecutar API:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Probar endpoint:
   ```bash
   curl -X POST "http://localhost:8000/ocr?document_type=ine" \
        -F "file=@../test_material/ineborrosa.jpg"
   ```
5. Tests unitarios: `pytest` (desde `backend/`).

## Frontend (Next.js + TS)

Ubicación: `frontend/ocr-frontend/`

1. Copiar variables y arrancar:
   ```bash
   cd frontend/ocr-frontend
   cp .env.local.example .env.local
   npm install
   npm run dev
   ```
2. La interfaz permite subir archivos, elegir tipo de documento y ver el JSON devuelto por la API.