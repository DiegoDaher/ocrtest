from fastapi import Depends, FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, Settings
from app.models import APIError, DocumentType, OCRRequest, OCRResponse
from app.ocr.service import run_ocr

app = FastAPI(title="OCR API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed to False
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ocr", response_model=OCRResponse, responses={400: {"model": APIError}, 500: {"model": APIError}})
def process_ocr(
    document_type: DocumentType,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> OCRResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío")

    # Validar tamaño máximo (10MB)
    max_size = 10 * 1024 * 1024
    if len(data) > max_size:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 10MB)")

    try:
        fields, metadata = run_ocr(
            data=data,
            filename=file.filename,
            content_type=file.content_type,
            document_type=document_type,
            settings=settings,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Formato de archivo inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el documento: {str(e)}")

    return OCRResponse(fields=fields, metadata=metadata)
