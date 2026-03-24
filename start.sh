#!/usr/bin/env sh
set -eu

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "${PORT:-8000}"