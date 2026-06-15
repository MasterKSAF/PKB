#!/bin/sh
set -eu

MIGRATION_RETRIES="${MIGRATION_RETRIES:-20}"
MIGRATION_RETRY_DELAY_SECONDS="${MIGRATION_RETRY_DELAY_SECONDS:-3}"

echo "[entrypoint] applying alembic migrations"

attempt=1
while [ "$attempt" -le "$MIGRATION_RETRIES" ]; do
  if python -m alembic upgrade head; then
    echo "[entrypoint] migrations applied successfully"
    exec python -m uvicorn rag_builder.main:app --host 0.0.0.0 --port "${APP_PORT:-8090}"
  fi

  echo "[entrypoint] migration attempt ${attempt}/${MIGRATION_RETRIES} failed; retry in ${MIGRATION_RETRY_DELAY_SECONDS}s"
  attempt=$((attempt + 1))
  sleep "$MIGRATION_RETRY_DELAY_SECONDS"
done

echo "[entrypoint] migrations failed after ${MIGRATION_RETRIES} attempts"
exit 1
