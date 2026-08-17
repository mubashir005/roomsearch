#!/bin/sh
# Container entrypoint for hosted deployments (e.g. Render) where the
# platform's command field doesn't reliably support shell chaining (&&).
set -e
alembic upgrade head
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
