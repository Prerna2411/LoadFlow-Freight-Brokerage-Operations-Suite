#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

alembic upgrade head

uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
