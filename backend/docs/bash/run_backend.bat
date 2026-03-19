@echo off
REM Script para ejecutar el backend OCR con variables de entorno correctas

setlocal enabledelayedexpansion

REM Rutas de Tesseract
set TESSERACT_ROOT=C:\Users\di3go\AppData\Local\Programs\Tesseract-OCR

REM Ruta de Poppler
set POPPLER_ROOT=C:\Users\di3go\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin

REM Establecer variables de entorno
set TESSDATA_PREFIX=%TESSERACT_ROOT%\tessdata
set TESSERACT_CMD=%TESSERACT_ROOT%\tesseract.exe
set PATH=%POPPLER_ROOT%;%TESSERACT_ROOT%\Library\bin;!PATH!

echo ==========================================
echo OCR API Backend - Iniciando
echo ==========================================
echo.
echo TESSDATA_PREFIX: %TESSDATA_PREFIX%
echo TESSERACT_CMD: %TESSERACT_CMD%
echo POPPLER_PATH: %POPPLER_ROOT%
echo.
echo Servidor escuchando en: http://localhost:8000
echo Docs disponibles en: http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener
echo ==========================================
echo.

REM Iniciar Uvicorn
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
