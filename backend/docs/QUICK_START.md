# GUIA RAPIDA - Ejecutar OCR API

## PASO 1: Terminal 1 - Backend

```bash
C:\Code\ocr_test> run_backend.bat
```

Deberías ver:
```
==========================================
OCR API Backend - Iniciando
==========================================

TESSDATA_PREFIX: C:\Users\di3go\AppData\Local\Programs\Tesseract-OCR\tessdata
TESSERACT_CMD: C:\Users\di3go\AppData\Local\Programs\Tesseract-OCR\tesseract.exe

Servidor escuchando en: http://localhost:8000
Docs disponibles en: http://localhost:8000/docs
```

## PASO 2: Terminal 2 - Frontend

```bash
C:\Code\ocr_test> run_frontend.bat
```

Deberías ver:
```
next dev

  ▲ Next.js 15.x
  - Local:        http://localhost:3000
```

## PASO 3: Abrir en Browser

```
http://localhost:3000
```

Carga un archivo PDF o imagen (INE o CURP) y presiona "Analizar documento"

---

## VERIFICACION RAPIDA

### Test de API (en otra terminal)
```bash
cd backend
python test_api.py
```

### Ver Swagger UI (Documentación de API)
```
http://localhost:8000/docs
```

---

## RESOLUCION DE PROBLEMAS

### Error: "Tesseract couldn't load language 'spa'"
✅ RESUELTO - Ejecutar `run_backend.bat` configura TESSDATA_PREFIX automáticamente

### Error: "Error opening data file tessdata/spa.traineddata"
→ Verificar que el archivo existe:
```bash
dir "C:\Users\di3go\AppData\Local\Programs\Tesseract-OCR\tessdata\spa.traineddata"
```

### Error 500 al subir archivo
→ Ver logs en la terminal del backend para mensaje de error específico
→ Usualmente significa que Tesseract no está configurado correctamente

### Error CORS en frontend
✅ YA SOLUCIONADO - Backend acepta todas las origins

### Puerto 8000 o 3000 en uso
```bash
# Cambiar puerto backend en run_backend.bat:
# Cambiar: --port 8000
# A:       --port 8001

# O matar proceso:
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

---

## ARCHIVOS IMPORTANTES

- `backend/.env` ................. Variables de env (TESSERACT_CMD, POPPLER_PATH)
- `backend/app/main.py` .......... API con manejo de errores
- `backend/app/ocr/service.py` . Motor OCR con Tesseract
- `frontend/ocr-frontend/src/app/page.tsx` .. UI principal
- `test_api.py` ................... Suite de tests

---

## FLUJO DEL OCR

1. Usuario carga archivo en Frontend (http://localhost:3000)
2. Frontend valida tipo (PDF/JPG/PNG/WebP)
3. Frontend envía a Backend (POST http://localhost:8000/ocr)
4. Backend:
   - Valida archivo (no vacío, < 10MB)
   - Si es PDF → Convierte a imágenes con poppler
   - Preprocessa: grayscale + blur + threshold
   - OCR: Tesseract en español
   - Extrae: nombre, domicilio, CURP, fecha nacimiento, vigencia
5. Frontend recibe JSON y muestra resultados

---

## LOGS ÚTILES

Backend devuelve:

**Success (200):**
```json
{
  "fields": {
    "name": "JUAN PEREZ",
    "address": "CALLE X 123",
    "curp": "PXJY800101HDFRRL09",
    "birth_date": "01/01/1980",
    "validity": "2025-12-31",
    "full_text": "..."
  },
  "metadata": {
    "pages": 1,
    "document_type": "ine"
  }
}
```

**Bad Request (400):**
```json
{
  "detail": "Archivo demasiado grande (máx 10MB)"
}
```

**Server Error (500):**
```json
{
  "detail": "Error al procesar el documento: Tesseract error message"
}
```

---

Escrito: 2025-03-18
Última verificación: Test suite + Tesseract configuration + Error handling
