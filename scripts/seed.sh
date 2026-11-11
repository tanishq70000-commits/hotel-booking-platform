#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Seeding database with initial rooms and sample reservations ==="
if [ -d "$PROJECT_ROOT/.venv" ]; then
    if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
    elif [ -f "$PROJECT_ROOT/.venv/Scripts/python.exe" ]; then
        PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
    else
        PYTHON_BIN="python3"
    fi
else
    PYTHON_BIN="python3"
fi

cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m scripts.seed
echo "=== Database seed completed successfully! ==="

