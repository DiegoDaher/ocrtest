#!/usr/bin/env python3
"""
Diagnostico rapido: Verifica que Backend + Frontend esten corriendo
"""
import socket
import sys
import time

def check_port(host, port, name):
    """Intenta conectar a un puerto para verificar si hay servidor"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"OK: {name} esta corriendo en {host}:{port}")
            return True
        else:
            print(f"FAIL: {name} NO esta corriendo en {host}:{port}")
            return False
    except Exception as e:
        print(f"ERROR: {name} - {e}")
        return False

print("=" * 60)
print("DIAGNOSTICO: Backend + Frontend")
print("=" * 60)
print()

# Esperar un poco
print("Verificando servidores...")
time.sleep(1)

# Verificar Backend
backend_ok = check_port("127.0.0.1", 8000, "Backend FastAPI")
print()

# Verificar Frontend
frontend_ok = check_port("127.0.0.1", 3000, "Frontend Next.js")
print()

print("=" * 60)
if backend_ok and frontend_ok:
    print("ESTADO: Ambos servidores corriendo")
    print()
    print("Abre navegador: http://localhost:3000")
elif backend_ok and not frontend_ok:
    print("ESTADO: Backend OK, pero Frontend NO esta corriendo")
    print()
    print("Ejecuta en Terminal 2:")
    print("  C:\\Code\\ocr_test> run_frontend.bat")
elif not backend_ok and frontend_ok:
    print("ESTADO: Frontend OK, pero Backend NO esta corriendo")
    print()
    print("Ejecuta en Terminal 1:")
    print("  C:\\Code\\ocr_test> run_backend.bat")
else:
    print("ESTADO: Ni Backend ni Frontend estan corriendo")
    print()
    print("Ejecuta en Terminal 1:")
    print("  C:\\Code\\ocr_test> run_backend.bat")
    print()
    print("Ejecuta en Terminal 2:")
    print("  C:\\Code\\ocr_test> run_frontend.bat")

print("=" * 60)
