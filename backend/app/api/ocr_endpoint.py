from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.models import APIError, DocumentType, OCRResponse
from app.ocr.service import run_ocr

router = APIRouter()


def _read_uploaded_data(file: UploadFile) -> bytes:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacÃ­o")

    max_size = 10 * 1024 * 1024
    if len(data) > max_size:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (mÃ¡x 10MB)")

    return data


@router.post("/ocr", response_model=OCRResponse, responses={400: {"model": APIError}, 500: {"model": APIError}})
def process_ocr(
    document_type: DocumentType,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> OCRResponse:
    data = _read_uploaded_data(file)

    try:
        fields, metadata = run_ocr(
            data=data,
            filename=file.filename,
            content_type=file.content_type,
            document_type=document_type,
            settings=settings,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Formato de archivo invÃ¡lido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el documento: {str(e)}")

    return OCRResponse(fields=fields, metadata=metadata)

