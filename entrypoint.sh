#!/usr/bin/env bash
set -euo pipefail

echo "=== [Entrypoint] Starting Hotel Reservation API container ==="

if [[ -z "${DATABASE_URL:-}" ]] || [[ "${DATABASE_URL}" == postgresql* ]]; then
  TARGET_HOST="${DB_HOST:-db}"
  TARGET_PORT="${DB_PORT:-5432}"
  TARGET_USER="${DB_USER:-hotel_app_user}"
  TARGET_DB="${DB_NAME:-hotel_booking}"

  echo "=== [Entrypoint] Waiting for PostgreSQL at ${TARGET_HOST}:${TARGET_PORT} ==="
  MAX_RETRIES=30
  RETRY_COUNT=0

  until pg_isready -h "${TARGET_HOST}" -p "${TARGET_PORT}" -U "${TARGET_USER}" -d "${TARGET_DB}" > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
      echo "=== [Entrypoint] ERROR: Database did not become ready within ${MAX_RETRIES} seconds ==="
      exit 1
    fi
    echo "=== [Entrypoint] Database not ready yet (${RETRY_COUNT}/${MAX_RETRIES}). Retrying in 1s... ==="
    sleep 1
  done
  echo "=== [Entrypoint] PostgreSQL is ready and accepting connections ==="
fi

echo "=== [Entrypoint] Running database migrations (Alembic) ==="
alembic upgrade head
echo "=== [Entrypoint] Migrations completed successfully. Starting application ==="

exec "$@"
