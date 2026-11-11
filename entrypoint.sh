#!/usr/bin/env bash
set -euo pipefail

echo "=== [Entrypoint] Running database migrations (Alembic) ==="
alembic upgrade head
echo "=== [Entrypoint] Migrations completed successfully. Starting application ==="

exec "$@"

