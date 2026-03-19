from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types for OCR extraction."""

    INE = "ine"
    CURP = "curp"


class OCRRequest(BaseModel):
    document_type: DocumentType = Field(..., description="Tipo de documento a procesar")


class OCRFields(BaseModel):
    full_text: str = Field(..., description="Texto completo reconocido por OCR")
    name: str | None = Field(default=None, description="Nombre de la persona")
    address: str | None = Field(default=None, description="Domicilio del documento")
    curp: str | None = Field(default=None, description="CURP detectada")
    birth_date: str | None = Field(default=None, description="Fecha de nacimiento detectada")
    validity: str | None = Field(default=None, description="Vigencia detectada")


class OCRResponse(BaseModel):
    fields: OCRFields
    metadata: dict[str, Any] = Field(default_factory=dict)


class APIError(BaseModel):
    detail: str
