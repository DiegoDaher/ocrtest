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

## Ejecucion con Docker

### 1) Construir imagen

```bash
cd ..
docker compose build backend
```

### 2) Levantar servicio

```bash
docker compose up -d backend
```

### 3) Verificar

```bash
curl http://localhost:8000/health
```

### 4) Logs

```bash
docker compose logs -f backend
```

Notas:
- El contenedor instala Tesseract, idioma espanol y Poppler automaticamente.
- La configuracion del servicio esta en `../docker-compose.yml` y `./.env.docker`.
