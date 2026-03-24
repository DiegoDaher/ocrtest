# Roadmap Ejecutable: Integracion ML Hibrida (OCR + ML)

## 1. Objetivo
Integrar modelos ML para mejorar extraccion documental sin romper el flujo actual basado en reglas.

Principio de compatibilidad:
- `POST /ocr` se mantiene igual.
- `OCRFields` y `OCRResponse` no se rompen.
- ML entra como capa adicional (fallback/reranking) sobre pipeline actual.

## 2. Arquitectura Objetivo (Hibrida)
Flujo objetivo:

```text
OCR actual + reglas -> resultado base
               -> ML extractor (opcional)
               -> comparador/reranker por campo
               -> fusion final (con confidence)
               -> OCRFields + metadata compatible
```

Regla base:
- Si ML no esta disponible, el sistema debe seguir operando con reglas actuales.

## 3. Fase 0: Preparacion de Datos
Entregables:
- formato de dataset definido
- guia de etiquetado
- data split fijo

### 3.1 Formato sugerido de dataset
Ejemplo JSONL por documento:

```json
{
  "doc_id": "ine_0001",
  "document_type": "ine",
  "image_path": "datasets/ine/train/ine_0001.jpg",
  "ocr_text": "...",
  "labels": {
    "name": "JUAN PEREZ",
    "address": "AV INSURGENTES 100",
    "curp": "PEPJ800101HDFXXX01",
    "birth_date": "01/01/1980",
    "validity": "2030"
  }
}
```

### 3.2 Splits
- Train: 70%
- Validation: 15%
- Test: 15%

Requisito:
- split por documento/persona para evitar leakage.

### 3.3 Versionado
- usar DVC, LakeFS o versionado por release en almacenamiento.
- cada entrenamiento referencia `dataset_version` explicito.

## 4. Fase 1: Modelo Base
Seleccion recomendada:
- Opcion A: LayoutLMv3 (si tienes OCR + bounding boxes).
- Opcion B: Donut (si quieres vision-to-seq con menos dependencia de OCR clasico).

Decision recomendada inicial:
- Iniciar con LayoutLMv3 para task de extraction por entidad/campo.

### 4.1 Estrategia de entrenamiento
- Entrenar por NER/slot-filling de campos objetivo.
- Modelos separados por tipo documental o multi-task con `document_type` como feature.
- Early stopping por F1 macro validacion.

## 5. Fase 2: Metricas y Criterios de Aceptacion
Metricas por campo:
- Precision, Recall, F1
- Exact Match (valor exacto normalizado)

Metricas por documento:
- all-fields exact match
- recall de campos criticos (`curp`, `name`)

Umbrales de salida recomendados (iniciales):
- F1 >= 0.92 para `curp`
- F1 >= 0.90 para `name`
- F1 >= 0.85 para `address`
- Exact Match global >= 0.80

Si no cumple:
- no activar ML en modo productivo.

## 6. Fase 3: Integracion Backend sin romper /ocr
Agregar un modulo interno, por ejemplo:
- `app/ocr/ml/engine.py`
- `app/ocr/ml/reranker.py`
- `app/ocr/ml/schema.py`

### 6.1 Contrato interno sugerido
```python
class MLFieldPrediction(TypedDict):
    value: str | None
    confidence: float

class MLPrediction(TypedDict):
    fields: dict[str, MLFieldPrediction]
    model_version: str
```

### 6.2 Politica de fusion (hibrida)
Por cada campo:
1. Tomar resultado de reglas como baseline.
2. Evaluar prediccion ML y confidence.
3. Si confidence >= umbral por campo y valida formato, usar ML.
4. Si confidence baja o invalido, mantener regla.

Ejemplo de umbral inicial:
- `curp`: 0.95
- `name`: 0.90
- `address`: 0.88
- `birth_date`: 0.90
- `validity`: 0.90

## 7. Fase 4: Confiabilidad, Drift y Logging
Registrar por request:
- tipo documento
- campos base vs ML
- confidence por campo
- campo final seleccionado
- latencia total

Monitoreo:
- tasa de override ML por campo
- tasa de rollback a reglas
- errores de inferencia
- drift de distribucion textual/visual

## 8. Fase 5: Despliegue Gradual
## 8.1 Shadow mode
- Ejecutar ML en paralelo sin afectar respuesta final.
- Comparar offline base vs ML por muestra real.

## 8.2 Canary
- activar fusion ML en porcentaje bajo de trafico.
- aumentar gradualmente si metrica estable.

## 8.3 Feature flag
Variables sugeridas:

```env
ML_ENABLED=false
ML_SHADOW_MODE=true
ML_MODEL_VERSION=layoutlmv3_v1
```

## 9. Stack Recomendado
Entrenamiento:
- Python, PyTorch, Transformers, Datasets.

Serving:
- FastAPI worker dedicado o servicio aparte (gRPC/HTTP).
- ONNX Runtime o TorchServe para optimizacion.

Evaluacion:
- scripts de evaluacion batch + reporte por campo.
- tracking de experimentos (MLflow/WandB).

MLOps:
- CI para validacion de modelo antes de release.
- registro de modelos versionados.

## 10. Seguridad y Cumplimiento
- Tratar documentos como PII sensible.
- Enmascarar campos sensibles en logs.
- Cifrado en reposo y transito para datasets/model artifacts.
- Politica de retencion y borrado de datos etiquetados.

## 11. Criterio de Exito
ML se considera listo para produccion cuando:
- supera umbrales de metrica definidos,
- reduce `missing_fields` sin subir falsos positivos,
- mantiene compatibilidad total con contrato actual de `/ocr`.

## 12. Siguiente Paso Tecnico
Implementar primero Fase 0-2 en entorno offline, luego Fase 3 en shadow mode.
