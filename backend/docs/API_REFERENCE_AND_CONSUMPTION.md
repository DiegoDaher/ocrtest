# API Reference y Consumo (Backend OCR)

## 1. Base URL
Default local:
- `http://localhost:8000`

## 2. Endpoints
## 2.1 GET /health
Verifica salud del servicio.

Ejemplo:

```bash
curl http://localhost:8000/health
```

Respuesta 200:

```json
{
  "status": "ok"
}
```

## 2.2 POST /ocr
Procesa un archivo y extrae campos segun tipo documental.

### Query params
- `document_type` (requerido):
- `ine`
- `curp`

### Body
- `multipart/form-data`
- Campo requerido: `file`

### Restricciones
- Tamano maximo: 10MB
- Soporta imagenes y PDF (segun conversion OCR)

## 3. Ejemplos de Consumo
## 3.1 cURL

```bash
curl -X POST "http://localhost:8000/ocr?document_type=ine" \
  -F "file=@./archivo_ine.pdf"
```

## 3.2 Frontend (fetch + FormData)
Ejemplo compatible con Next.js o cualquier cliente browser:

```ts
const formData = new FormData();
formData.append("file", selectedFile);

const response = await fetch(`${API_BASE}/ocr?document_type=${documentType}`, {
  method: "POST",
  body: formData,
});

const payload = await response.json();
if (!response.ok) {
  throw new Error(payload?.detail ?? "Error de API");
}

const fields = payload.fields;
const metadata = payload.metadata;
```

## 4. Contrato de Respuesta (OCRResponse)
Estructura estable:

```json
{
  "fields": {
    "full_text": "string",
    "name": "string|null",
    "address": "string|null",
    "curp": "string|null",
    "clave": "string|null",
    "certification_status": "string|null",
    "is_certified": "boolean|null",
    "birth_date": "string|null",
    "validity": "string|null"
  },
  "metadata": {
    "pages": 1,
    "document_type": "ine|curp",
    "ocr_strategy": [],
    "extraction_quality": {
      "missing_fields": [],
      "needs_review": false
    }
  }
}
```

## 5. Significado de Fields
- `full_text`: texto OCR consolidado de todas las paginas/regiones seleccionadas.
- `name`: nombre detectado.
- `address`: domicilio detectado (normalmente relevante en INE).
- `curp`: CURP detectada.
- `clave`: para documentos CURP, suele mapear a la CURP extraida.
- `certification_status`: estado de certificacion CURP si aparece en el documento.
- `is_certified`: indicador booleano de certificacion.
- `birth_date`: fecha de nacimiento detectada.
- `validity`: vigencia detectada.

## 6. Ejemplos por Tipo
## 6.1 Caso INE (200)

```json
{
  "fields": {
    "full_text": "...",
    "name": "JUAN PEREZ",
    "address": "AV INSURGENTES 100, CDMX",
    "curp": "PEPJ800101HDFXXX01",
    "clave": null,
    "certification_status": null,
    "is_certified": null,
    "birth_date": "01/01/1980",
    "validity": "2030"
  },
  "metadata": {
    "pages": 1,
    "document_type": "ine",
    "ocr_strategy": [],
    "extraction_quality": {
      "missing_fields": [],
      "needs_review": false
    }
  }
}
```

## 6.2 Caso CURP (200)

```json
{
  "fields": {
    "full_text": "...",
    "name": "JUAN PEREZ",
    "address": null,
    "curp": "PEPJ800101HDFXXX01",
    "clave": "PEPJ800101HDFXXX01",
    "certification_status": "CURP Certificada: verificada con el Registro Civil",
    "is_certified": true,
    "birth_date": "01/01/1980",
    "validity": null
  },
  "metadata": {
    "pages": 1,
    "document_type": "curp",
    "ocr_strategy": [],
    "extraction_quality": {
      "missing_fields": [],
      "needs_review": false
    }
  }
}
```

## 7. Manejo de Errores
Modelo de error:

```json
{
  "detail": "mensaje de error"
}
```

Tabla operativa:

Codigo | Caso | Ejemplo de detail
- 400 | Archivo sin nombre | `Archivo sin nombre`
- 400 | Archivo vacio | `Archivo vacio`
- 400 | Archivo grande | `Archivo demasiado grande (max 10MB)`
- 400 | Formato invalido | `Formato de archivo invalido: ...`
- 500 | Error interno OCR | `Error al procesar el documento: ...`

## 8. Compatibilidad Publica
Se mantiene sin cambios:
- `DocumentType`: `ine`, `curp`
- `OCRFields`
- `OCRResponse`
- `POST /ocr`

Notas para clientes:
- Tratar campos como opcionales (`null`) segun calidad documental.
- Usar `extraction_quality.needs_review` para decidir validacion manual.
