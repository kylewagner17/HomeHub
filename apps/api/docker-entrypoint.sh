#!/bin/sh
set -e
cd /app
alembic upgrade head
exec uvicorn homehub.main:app --host 0.0.0.0 --port 8000 --app-dir src
