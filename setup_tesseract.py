#!/usr/bin/env python3
"""
Configurar Tesseract y variables de entorno para OCR
"""
import os
import sys
import subprocess
from pathlib import Path

def check_tesseract_installation():
    """Verifica si Tesseract está instalado"""
    common_paths = [
        r"C:\Users\di3go\AppData\Local\Programs\Tesseract-OCR",
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
    ]

    for path in common_paths:
        exe_path = Path(path) / "tesseract.exe"
        if exe_path.exists():
            print(f"✅ Tesseract encontrado en: {path}")
            return path

    print("❌ Tesseract no encontrado en rutas estándar")
    print("   Instálalo desde: https://github.com/UB-Mannheim/tesseract/wiki")
    return None

def setup_env_file(tesseract_path):
    """Crea y configura el archivo .env"""
    env_content = f"""# Backend Configuration
API_PREFIX=/api
APP_NAME=OCR API
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Tesseract Configuration
TESSERACT_CMD={tesseract_path}\\tesseract.exe

# Poppler Configuration
POPPLER_PATH={tesseract_path}\\Library\\bin
"""

    env_file = Path("backend/.env")
    env_file.write_text(env_content)
    print(f"✅ Configurado: {env_file}")

def set_environment_variables(tesseract_path):
    """Establece variables de entorno para la sesión actual"""
    os.environ["TESSDATA_PREFIX"] = str(Path(tesseract_path) / "tessdata")
    os.environ["TESSERACT_CMD"] = str(Path(tesseract_path) / "tesseract.exe")

    print(f"✅ TESSDATA_PREFIX: {os.environ['TESSDATA_PREFIX']}")
    print(f"✅ TESSERACT_CMD: {os.environ['TESSERACT_CMD']}")

def verify_pytesseract():
    """Verifica que pytesseract funcione"""
    try:
        import pytesseract
        print("✅ pytesseract importado correctamente")
        return True
    except ImportError:
        print("❌ pytesseract no está instalado")
        print("   Ejecuta: pip install -r requirements.txt")
        return False

def test_ocr():
    """Test rápido de OCR"""
    try:
        import pytesseract
        from PIL import Image
        import io

        # Crear imagen de prueba simple
        img = Image.new('RGB', (200, 100), color='white')

        # Intentar OCR
        text = pytesseract.image_to_string(img, lang="spa")
        print("✅ Tesseract funcionando")
        return True
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        return False

def main():
    print("=" * 60)
    print("Setup Tesseract para OCR API")
    print("=" * 60)

    # 1. Verificar instalación
    print("\n[1] Verificando Tesseract...")
    tesseract_path = check_tesseract_installation()
    if not tesseract_path:
        sys.exit(1)

    # 2. Configurar .env
    print("\n[2] Configurando .env...")
    setup_env_file(tesseract_path)

    # 3. Establecer variables de entorno
    print("\n[3] Estableciendo variables de entorno...")
    set_environment_variables(tesseract_path)

    # 4. Verificar pytesseract
    print("\n[4] Verificando pytesseract...")
    if not verify_pytesseract():
        print("\n   Instalando dependencias...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
            cwd=str(Path.cwd())
        )

    # 5. Test rápido
    print("\n[5] Test de OCR...")
    test_ocr()

    print("\n" + "=" * 60)
    print("Setup completado!")
    print("=" * 60)
    print("\nProximos pasos:")
    print("   1. cd backend")
    print("   2. uvicorn app.main:app --reload")
    print("\n   En otra terminal:")
    print("   1. cd frontend/ocr-frontend")
    print("   2. npm run dev")
    print("\n   Browser: http://localhost:3000")

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    main()
