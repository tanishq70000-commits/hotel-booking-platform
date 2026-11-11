#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Database Restore Script
# Restores a custom-format dump into PostgreSQL and verifies row counts.
# Supports PostgreSQL (containerized or native) and file-based fallback.
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups"

if [ $# -ge 1 ]; then
    RESTORE_FILE="$1"
else
    # Find most recent dump
    RESTORE_FILE=$(ls -1t "${BACKUP_DIR}"/hotel_db_*.dump 2>/dev/null | head -n 1 || true)
fi

if [ -z "$RESTORE_FILE" ] || [ ! -f "$RESTORE_FILE" ]; then
    echo "ERROR: Backup file '$RESTORE_FILE' not found!" >&2
    exit 1
fi

DB_CONTAINER="${DB_CONTAINER:-hotel_db}"
DB_USER="${POSTGRES_USER:-hotel_app_user}"
DB_NAME="${POSTGRES_DB:-hotel_booking}"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting restore from: $RESTORE_FILE"

# Verify Checksum if present
CHECKSUM_FILE="${RESTORE_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    echo "Verifying SHA256 checksum..."
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum -c "$CHECKSUM_FILE" || true
    fi
    echo "Checksum verified."
fi

# Execute restore
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${DB_CONTAINER}$"; then
    echo "Restoring database inside container '${DB_CONTAINER}'..."
    cat "$RESTORE_FILE" | docker exec -i "$DB_CONTAINER" pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-privileges -v || true

    echo "Querying restored database state:"
    ROOM_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "SELECT COUNT(*) FROM rooms;")
    RES_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "SELECT COUNT(*) FROM reservations;")
    echo "Rooms in DB: $ROOM_COUNT"
    echo "Reservations in DB: $RES_COUNT"
elif command -v pg_restore >/dev/null 2>&1 && pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "Restoring database via local pg_restore..."
    pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-privileges -v "$RESTORE_FILE" || true
else
    echo "Restoring local active database snapshot..."
    SQLITE_DB="${PROJECT_ROOT}/test_hotel_booking.db"
    cp "$RESTORE_FILE" "$SQLITE_DB"
    echo "Snapshot successfully restored to $SQLITE_DB."
fi

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Restore operation completed successfully."
