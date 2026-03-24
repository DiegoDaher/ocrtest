from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ocr_endpoint import router as ocr_router
from app.config import get_settings

app = FastAPI(title="OCR API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ocr_router)

