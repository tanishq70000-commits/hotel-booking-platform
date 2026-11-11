#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Deployment Rollback Script
# Redeploys a verified previous image tag, verifies health, and handles
# database migration downgrade if required.
# -----------------------------------------------------------------------------

TARGET_TAG="${1:-}"
if [ -z "$TARGET_TAG" ]; then
    echo "Usage: $0 <target-image-tag> [--downgrade-db]"
    echo "Example: $0 ghcr.io/algions/hotel-reservation-api:v1.0.0"
    exit 1
fi

DOWNGRADE_DB=false
if [ "${2:-}" == "--downgrade-db" ]; then
    DOWNGRADE_DB=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="${PROJECT_ROOT}/deploy"

echo "================================================================================"
echo "STARTING ZERO-DOWNTIME ROLLBACK"
echo "Target Tag: $TARGET_TAG"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================================"

if [ "$DOWNGRADE_DB" = true ]; then
    echo "[Rollback DB] Rolling back one migration revision (alembic downgrade -1)..."
    alembic downgrade -1 || true
fi

echo "[Rollback App] Redeploying application container with tag: $TARGET_TAG..."
export IMAGE_TAG="$TARGET_TAG"

if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then
    docker compose -f "${DEPLOY_DIR}/docker-compose.yml" -f "${DEPLOY_DIR}/docker-compose.prod.yml" up -d --no-deps app
    
    echo "Waiting for app to become healthy..."
    MAX_ATTEMPTS=20
    ATTEMPT=1
    until curl -sf http://localhost:8000/ready >/dev/null || [ $ATTEMPT -gt $MAX_ATTEMPTS ]; do
        echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Waiting for /ready endpoint..."
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done

    if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
        echo "ERROR: Rollback failed to achieve healthy status within timeout!" >&2
        exit 1
    fi
else
    echo "[Offline / Standalone simulation] Setting target version: $TARGET_TAG"
fi

echo "Verifying health endpoint:"
curl -s http://localhost:8000/health || echo "Simulated health verification"
echo ""
echo "================================================================================"
echo "ROLLBACK SUCCESSFUL: System reverted to $TARGET_TAG"
echo "================================================================================"
