# Configuracion Final Backend OCR (Actualizada)

## 1. Requisitos
## 1.1 Runtime Python
Instalar desde `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1.2 Dependencias de sistema
- Tesseract OCR
- Poppler (requerido para PDF)

## 2. Variables de entorno
Configurar `backend/.env`:

```env
TESSERACT_CMD=C:\ruta\a\tesseract.exe
TESSDATA_PREFIX=C:\ruta\a\tesseract\tessdata
POPPLER_PATH=C:\ruta\a\poppler\Library\bin
```

Descripcion:
- `TESSERACT_CMD`: ejecutable o directorio de Tesseract.
- `TESSDATA_PREFIX`: carpeta con `spa.traineddata`.
- `POPPLER_PATH`: carpeta donde vive `pdftoppm.exe`.

## 3. Arranque
Desde `backend/`:

```powershell
uvicorn app.main:app --reload
```

## 4. Verificacion
Health:

```bash
curl http://localhost:8000/health
```

OCR con archivo:

```bash
curl -X POST "http://localhost:8000/ocr?document_type=curp" -F "file=@./curp.pdf"
```

## 5. Errores comunes
Problema | Accion
- `Tesseract not found` | validar `TESSERACT_CMD` y `where tesseract`
- `spa.traineddata not found` | validar `TESSDATA_PREFIX` y archivo de idioma
- error de PDF | validar `POPPLER_PATH` y `pdftoppm.exe`
- HTTP 400 | revisar validaciones de archivo y formato
- HTTP 500 | revisar logs del backend para detalle de OCR/parsing

## 6. Contrato y compatibilidad
Sin cambios en contrato publico:
- `POST /ocr`
- `DocumentType` (`ine`, `curp`)
- `OCRFields`
- `OCRResponse`

## 7. Siguientes lecturas
- `backend/docs/SERVICE_BACKEND_GUIDE.md`
- `backend/docs/API_REFERENCE_AND_CONSUMPTION.md`
- `backend/docs/EXTRACTION_EXTENSION_GUIDE.md`
- `backend/docs/ML_HYBRID_IMPLEMENTATION_ROADMAP.md`
