#!/bin/bash
# Script para ejecutar el backend OCR con variables de entorno correctas

# Rutas de Tesseract
TESSERACT_ROOT="C:\Users\di3go\AppData\Local\Programs\Tesseract-OCR"

# Establecer variables de entorno
export TESSDATA_PREFIX="${TESSERACT_ROOT}\tessdata"
export TESSERACT_CMD="${TESSERACT_ROOT}\tesseract.exe"
export PATH="${TESSERACT_ROOT}\Library\bin:${PATH}"

echo "=========================================="
echo "OCR API Backend - Iniciando"
echo "=========================================="
echo ""
echo "TESSDATA_PREFIX: $TESSDATA_PREFIX"
echo "TESSERACT_CMD: $TESSERACT_CMD"
echo ""
echo "Servidor escuchando en: http://localhost:8000"
echo "Docs disponibles en: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener"
echo "=========================================="
echo ""

# Iniciar Uvicorn
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
