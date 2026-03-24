from __future__ import annotations

from io import BytesIO

from PIL import Image

from app.config import Settings
from app.ocr.pipeline import ingestion


def _build_image_bytes(fmt: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (24, 24), color="white").save(buffer, format=fmt)
    return buffer.getvalue()


def test_load_images_from_image_bytes_returns_single_page() -> None:
    settings = Settings()
    image_bytes = _build_image_bytes("PNG")

    pages = ingestion.load_images(
        data=image_bytes,
        filename="sample.png",
        content_type="image/png",
        settings=settings,
    )

    assert len(pages) == 1
    assert pages[0].shape[0] > 0
    assert pages[0].shape[1] > 0


def test_load_images_from_pdf_uses_pdf_converter(monkeypatch) -> None:
    called: dict[str, object] = {}

    def fake_convert_from_bytes(data: bytes, fmt: str, poppler_path: str | None) -> list[Image.Image]:
        called["data"] = data
        called["fmt"] = fmt
        called["poppler_path"] = poppler_path
        return [Image.new("RGB", (10, 10), color="white"), Image.new("RGB", (11, 11), color="white")]

    monkeypatch.setattr(ingestion, "convert_from_bytes", fake_convert_from_bytes)

    settings = Settings(poppler_path="C:/fake/poppler")
    pages = ingestion.load_images(
        data=b"%PDF-1.4 fake",
        filename="sample.pdf",
        content_type="application/pdf",
        settings=settings,
    )

    assert called["fmt"] == "jpeg"
    assert called["poppler_path"] == "C:/fake/poppler"
    assert len(pages) == 2

