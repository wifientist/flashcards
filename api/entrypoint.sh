#!/usr/bin/env sh
set -e

# Apply database migrations before serving.
alembic upgrade head

# Optionally bootstrap the first admin (no-op if it already exists).
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  python seed_admin.py || echo "seed_admin: skipped (continuing)"
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
