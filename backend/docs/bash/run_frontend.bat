@echo off
REM Script para ejecutar el frontend OCR

setlocal enabledelayedexpansion

echo ==========================================
echo OCR Frontend - Iniciando
echo ==========================================
echo.
echo Asegurate que el backend esta corriendo en http://localhost:8000
echo.
echo Frontend estara disponible en: http://localhost:3000
echo.
echo Presiona Ctrl+C para detener
echo ==========================================
echo.

REM Iniciar Next.js dev server
cd frontend\ocr-frontend
npm run dev

pause
