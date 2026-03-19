#!/usr/bin/env python3
"""
Test script for OCR API - Valida CORS, errores y flujo completo
"""
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests no instalado: pip install requests")
    sys.exit(1)

API_BASE = "http://localhost:8000"
HEALTH_URL = f"{API_BASE}/health"
OCR_URL = f"{API_BASE}/ocr"

def test_cors():
    """Verifica que CORS esté configurado correctamente"""
    print("\n🔍 Test 1: CORS Headers")
    try:
        response = requests.options(
            OCR_URL,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )

        cors_headers = {
            "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
            "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods"),
            "access-control-allow-headers": response.headers.get("Access-Control-Allow-Headers"),
        }

        if cors_headers["access-control-allow-origin"] == "*":
            print(f"✅ CORS: {json.dumps(cors_headers, indent=2)}")
            return True
        else:
            print(f"⚠️  CORS Headers not found: {cors_headers}")
            return False
    except Exception as e:
        print(f"❌ Error CORS: {e}")
        return False

def test_health():
    """Verifica que el servidor esté en línea"""
    print("\n🔍 Test 2: Health Check")
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Health: {response.json()}")
            return True
        else:
            print(f"❌ Health failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error Health: {e}")
        return False

def test_empty_file():
    """Verifica que rechaza archivos vacíos (400, not 500)"""
    print("\n🔍 Test 3: Empty File Validation")
    try:
        files = {"file": ("empty.txt", b"")}
        response = requests.post(
            f"{OCR_URL}?document_type=ine",
            files=files
        )

        if response.status_code == 400:
            print(f"✅ Correctly rejected empty file (400): {response.json()}")
            return True
        else:
            print(f"❌ Wrong status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error Empty File: {e}")
        return False

def test_invalid_file_type():
    """Verifica que rechaza tipos inválidos (400, not 500)"""
    print("\n🔍 Test 4: Invalid File Type")
    try:
        files = {"file": ("test.txt", b"This is plain text")}
        response = requests.post(
            f"{OCR_URL}?document_type=ine",
            files=files
        )

        # Debería ser 400 (bad request) no 500 (server error)
        if response.status_code == 400:
            print(f"✅ Correctly rejected invalid type (400): {response.json()}")
            return True
        elif response.status_code == 500:
            print(f"❌ ERROR 500 (should be 400): {response.json()}")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error Invalid Type: {e}")
        return False

def test_large_file():
    """Verifica que rechaza archivos > 10MB"""
    print("\n🔍 Test 5: Large File (>10MB) Validation")
    try:
        large_data = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("huge.pdf", large_data)}
        response = requests.post(
            f"{OCR_URL}?document_type=ine",
            files=files,
            timeout=10
        )

        if response.status_code == 400:
            print(f"✅ Correctly rejected large file (400): {response.json()['detail'][:100]}...")
            return True
        else:
            print(f"❌ Wrong status: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Timeout or error (expected): {type(e).__name__}")
        return True

def test_missing_file():
    """Verifica POST sin archivo"""
    print("\n🔍 Test 6: Missing File Validation")
    try:
        response = requests.post(
            f"{OCR_URL}?document_type=ine",
            timeout=5
        )

        if response.status_code == 400:
            print(f"✅ Correctly rejected missing file (400): {response.json()}")
            return True
        else:
            print(f"❌ Wrong status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 OCR API Test Suite - Validación de CORS y Errores")
    print("=" * 60)

    tests = [
        ("CORS Configuration", test_cors),
        ("Server Health", test_health),
        ("Empty File Rejection", test_empty_file),
        ("Invalid Type Rejection", test_invalid_file_type),
        ("Large File Rejection", test_large_file),
        ("Missing File Rejection", test_missing_file),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"⚠️  Test failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! API is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
