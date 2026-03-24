# Guia Tecnica del Servicio Backend OCR

## 1. Objetivo
Este documento explica como funciona el backend OCR actual, sus dependencias, configuracion, flujo interno y practicas de operacion.

Contrato publico estable:
- Endpoint: `POST /ocr`
- Tipos de documento: `ine`, `curp`
- Modelos de respuesta: `OCRFields`, `OCRResponse`

## 2. Arquitectura Actual
Pipeline real en produccion:

1. API FastAPI recibe request (`app/main.py`, `app/api/ocr_endpoint.py`).
2. Endpoint valida archivo y parametros basicos.
3. Endpoint delega a `run_ocr(...)` (`app/ocr/service.py`).
4. `run_ocr` ejecuta pipeline OCR modular:
- ingestion (`app/ocr/pipeline/ingestion.py`)
- preprocess (`app/ocr/pipeline/preprocess.py`)
- recognition (`app/ocr/pipeline/recognition.py`)
- scoring (`app/ocr/pipeline/scoring.py`)
- orchestration (`app/ocr/pipeline/orchestration.py`)
5. Texto OCR final se envia al extractor por tipo documental (`app/ocr/extractors/*`).
6. Se construye `OCRFields` y `metadata` y se retorna `OCRResponse`.

Diagrama resumido:

```text
HTTP Request (multipart/form-data)
  -> process_ocr (/ocr)
  -> _read_uploaded_data (validaciones)
  -> run_ocr
  -> load_images (PDF/imagen)
  -> run_ocr_pipeline (OCR por pagina y region)
  -> extract_fields (INE o CURP)
  -> metadata (quality + estrategia)
  -> HTTP 200 OCRResponse
```

## 3. Flujo de Procesamiento Detallado
### 3.1 Ingestion
- Detecta si el archivo es PDF por extension o `content_type`.
- PDF: convierte paginas con `pdf2image` + Poppler.
- Imagen: abre con Pillow y convierte a arreglo OpenCV BGR.

### 3.2 Preprocesamiento
- Escala minima para OCR.
- Correccion de inclinacion (deskew).
- Variantes de umbralizado y contraste.
- Deteccion de regiones de documento en la pagina para mejorar OCR en PDFs.

### 3.3 Recognition + Scoring
- Ejecuta Tesseract con varias estrategias (`psm` distintos).
- Puntua candidatos por senal documental (keywords, CURP, fechas, limpieza del texto).
- Combina mejores candidatos cuando agregan informacion util sin duplicar lineas.

### 3.4 Extraccion de Campos
- `ExtractorRegistry` resuelve extractor por `DocumentType`.
- `INEExtractor` y `CURPExtractor` aplican reglas robustas (keywords tolerantes, fallbacks, MRZ cuando aplica).
- Devuelve siempre `OCRFields` con los mismos campos del contrato.

### 3.5 Metadata
`run_ocr` retorna metadata con:
- `pages`
- `document_type`
- `ocr_strategy` (resumen por pagina/region/candidatos)
- `extraction_quality` (`missing_fields`, `needs_review`)

## 4. Dependencias Requeridas
## 4.1 Python (requirements)
- `fastapi`
- `uvicorn[standard]`
- `python-multipart`
- `pillow`
- `opencv-python-headless`
- `pytesseract`
- `pdf2image`
- `pdfplumber` (instalada; uso opcional para futuras mejoras)
- `numpy`
- `pydantic-settings`
- `python-dotenv`
- `pytest`

## 4.2 Dependencias del sistema
- Tesseract OCR instalado en OS.
- Poppler instalado para conversion de PDF a imagen.

## 5. Configuracion
Variables de entorno backend (`backend/.env`):

```env
TESSERACT_CMD=C:\ruta\a\tesseract.exe
TESSDATA_PREFIX=C:\ruta\a\tesseract\tessdata
POPPLER_PATH=C:\ruta\a\poppler\Library\bin
```

Notas:
- `TESSERACT_CMD` puede ser ruta a ejecutable o directorio.
- `POPPLER_PATH` se usa cuando se procesan PDFs.

## 6. Arranque Windows-First
Desde `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Validaciones rapidas:

```powershell
curl http://localhost:8000/health
```

Swagger:
- `http://localhost:8000/docs`

## 7. Manejo de Errores Operativos
Errores de entrada (`400`):
- archivo sin nombre
- archivo vacio
- archivo mayor a 10MB
- formato/decodificacion invalida

Errores de procesamiento (`500`):
- excepciones no controladas en OCR o parsing

Recomendacion operativa:
- revisar logs del backend para confirmar si el problema es ruta de Tesseract/Poppler, idioma OCR, archivo corrupto o timeout operativo.

## 8. Troubleshooting Windows
Problema comun | Causa probable | Accion recomendada
- Tesseract no encontrado | `TESSERACT_CMD` invalido | validar ruta y ejecutar `where tesseract`
- No carga idioma `spa` | `TESSDATA_PREFIX` invalido o falta `spa.traineddata` | validar carpeta `tessdata`
- Error al abrir PDF | Poppler no disponible | validar `POPPLER_PATH` y `pdftoppm.exe`
- Error en archivo subido | formato no valido o corrupto | probar con imagen/PDF conocido
- Extraccion incompleta | baja calidad de imagen | mejorar input o usar fallback/manual review

## 9. Limites y Compatibilidad
- Servicio actual es sincrono.
- No hay entrenamiento ML en runtime productivo.
- Contrato API y modelos publicos se mantienen estables.

## 10. Referencias Relacionadas
- `backend/docs/API_REFERENCE_AND_CONSUMPTION.md`
- `backend/docs/EXTRACTION_EXTENSION_GUIDE.md`
- `backend/docs/ML_HYBRID_IMPLEMENTATION_ROADMAP.md`
- `backend/docs/MODULARIZATION_CHECKLIST.md`
