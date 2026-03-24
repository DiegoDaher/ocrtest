# Guia de Extension de Extraccion (Reglas + Extractores)

## 1. Objetivo
Definir como agregar nuevas capacidades de extraccion sin romper contratos publicos ni degradar los casos actuales.

Contrato a preservar:
- `POST /ocr`
- `OCRFields`
- `OCRResponse`

## 2. Arquitectura de Extraccion Actual
Componentes:
- `app/ocr/fields.py`: fachada de compatibilidad.
- `app/ocr/extractors/registry.py`: registro y resolucion por `DocumentType`.
- `app/ocr/extractors/common.py`: utilidades compartidas (normalizacion, regex, validadores).
- `app/ocr/extractors/ine.py`: reglas de INE.
- `app/ocr/extractors/curp.py`: reglas de CURP.
- `app/ocr/extractors/template.py`: plantilla para extractor nuevo.

## 3. Proceso para Agregar Nuevo Tipo de Documento
Paso 1: agregar enum en `app/models.py`

```python
class DocumentType(str, Enum):
    INE = "ine"
    CURP = "curp"
    PASAPORTE = "pasaporte"  # nuevo
```

Paso 2: crear extractor nuevo en `app/ocr/extractors/pasaporte.py`

```python
from app.models import OCRFields

class PasaporteExtractor:
    def extract(self, text: str) -> OCRFields:
        # aplicar reglas
        return OCRFields(
            full_text=text,
            name=None,
            address=None,
            curp=None,
            clave=None,
            certification_status=None,
            is_certified=None,
            birth_date=None,
            validity=None,
        )
```

Paso 3: registrar extractor en `registry.py`

```python
registry.register(DocumentType.PASAPORTE, PasaporteExtractor().extract)
```

Paso 4: pruebas de regresion
- agregar tests unitarios del extractor nuevo.
- validar que pruebas de INE/CURP sigan pasando.
- validar contrato de respuesta (campos y metadata).

Paso 5: validacion funcional
- probar con muestras reales del documento nuevo.
- confirmar `missing_fields` y `needs_review` en metadata.

## 4. Buenas Practicas de Reglas
- Normalizar texto antes de extraer.
- Tolerar ruido OCR en keywords (`N0MBRE`, `V1GENCIA`, etc).
- Definir validadores por campo (ejemplo CURP, fechas).
- Incluir fallbacks por contexto (lineas siguientes, MRZ, bloques de direccion).
- No mezclar reglas de tipos distintos en un solo extractor.

## 5. Criterios de Calidad Minimos
Para aprobar cambios de extraccion:
- Exactitud estable en casos actuales (INE/CURP) sin regresiones.
- Nuevos casos cubiertos con tests representativos.
- `full_text` siempre presente.
- Campos no detectados deben quedar en `null`, no inventados.

## 6. Checklist de Entrega
- [ ] Nuevo `DocumentType` agregado.
- [ ] Extractor implementado.
- [ ] Extractor registrado en registry.
- [ ] Tests unitarios nuevos.
- [ ] Tests existentes sin regresion.
- [ ] Ejemplos de request/response actualizados en docs.
- [ ] Verificado que `/ocr` no cambia contrato.

## 7. Errores Comunes a Evitar
- Agregar logica del tipo nuevo dentro de extractor INE/CURP.
- Cambiar nombre de campos en `OCRFields`.
- Depender de un unico patron estricto sin fallback.
- Mezclar decisiones de OCR pipeline con reglas de extraccion.

## 8. Referencias
- `backend/docs/SERVICE_BACKEND_GUIDE.md`
- `backend/docs/API_REFERENCE_AND_CONSUMPTION.md`
- `backend/docs/MODULARIZATION_CHECKLIST.md`
