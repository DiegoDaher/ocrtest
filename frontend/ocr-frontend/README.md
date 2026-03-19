## OCR Frontend

Interfaz en Next.js + TypeScript que permite subir PDFs/imagenes, seleccionar documento INE o CURP y visualizar la respuesta JSON del backend FastAPI.

### Variables de entorno

```bash
cp .env.local.example .env.local
# Ajusta NEXT_PUBLIC_OCR_API si el backend corre en otra URL
```

### Scripts

```bash
npm install        # una sola vez
npm run dev        # arranca http://localhost:3000
npm run lint       # verifica el código
npm run build      # compila en modo producción
```

### Flujo

1. Inicia el backend (`uvicorn app.main:app --reload` en ../backend).
2. Ejecuta `npm run dev` y abre el sitio.
3. Sube un archivo desde `test_material/` o arrastra uno propio.
4. Observa los campos parseados, el texto OCR completo y la metadata del backend.
