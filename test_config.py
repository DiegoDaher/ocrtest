#!/usr/bin/env python3
"""
Test rapido: Verificar que Tesseract y Poppler esten configurados correctamente
"""
import os
import sys
from pathlib import Path

# Cargar .env
from dotenv import load_dotenv
load_dotenv("backend/.env")

print("=" * 60)
print("TEST: Tesseract + Poppler Configuration")
print("=" * 60)

# 1. Verificar Tesseract
print("\n[1] TESSERACT")
tesseract_cmd = os.getenv("TESSERACT_CMD")
print(f"  TESSERACT_CMD: {tesseract_cmd}")

if tesseract_cmd and Path(tesseract_cmd).exists():
    print("  OK: Tesseract encontrado")
else:
    print("  FAIL: Tesseract NO encontrado")

# 2. Verificar tessdata (idioma espanol)
print("\n[2] TESSDATA (Spanish language)")
tessdata_prefix = os.getenv("TESSDATA_PREFIX")

# Si no esta en env, intenta obtenerlo del TESSERACT_CMD
if not tessdata_prefix and tesseract_cmd:
    tessdata_prefix = str(Path(tesseract_cmd).parent.parent / "tessdata")

print(f"  TESSDATA_PREFIX: {tessdata_prefix}")

if tessdata_prefix:
    spa_file = Path(tessdata_prefix) / "spa.traineddata"
    if spa_file.exists():
        print(f"  OK: spa.traineddata encontrado")
    else:
        print(f"  FAIL: spa.traineddata NO encontrado en {tessdata_prefix}")

# 3. Verificar Poppler
print("\n[3] POPPLER")
poppler_path = os.getenv("POPPLER_PATH")
print(f"  POPPLER_PATH: {poppler_path}")

if poppler_path and Path(poppler_path).exists():
    print("  OK: Poppler encontrado")
    # Buscar pdftoimage o pdftoppm
    pdftoppm = Path(poppler_path) / "pdftoppm.exe"
    pdftoimage = Path(poppler_path) / "pdftoimage.exe"

    if pdftoppm.exists():
        print(f"  OK: pdftoppm.exe encontrado")
    elif pdftoimage.exists():
        print(f"  OK: pdftoimage.exe encontrado")
    else:
        print(f"  WARN: Poppler utils no encontrados en {poppler_path}")
else:
    print("  FAIL: Poppler NO encontrado")

# 4. Test pytesseract
print("\n[4] PYTESSERACT TEST")
try:
    import pytesseract
    from PIL import Image

    # Crear imagen de prueba
    img = Image.new('RGB', (200, 50), color='white')
    text = pytesseract.image_to_string(img, lang="spa")
    print("  OK: pytesseract funcionando")
except Exception as e:
    print(f"  FAIL: {e}")

# 5. Test pdf2image
print("\n[5] PDF2IMAGE + POPPLER TEST")
try:
    from pdf2image import convert_from_bytes
    print("  OK: pdf2image importado")
except Exception as e:
    print(f"  FAIL: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETADO")
print("=" * 60)
