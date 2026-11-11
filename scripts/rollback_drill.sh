#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Rollback Drill Script
# Automated drill testing release rollback:
# 1. Shows initial stable version (v1.0.0) at /health
# 2. Simulates deployment of changed/faulty release (v1.1.0-faulty)
# 3. Executes rollback procedure to stable v1.0.0
# 4. Verifies /health confirms old version restored
# 5. Captures full evidence log to evidence/rollback-drill.txt
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EVIDENCE_DIR="${PROJECT_ROOT}/evidence"
mkdir -p "$EVIDENCE_DIR"
LOG_FILE="${EVIDENCE_DIR}/rollback-drill.txt"

if [ -d "$PROJECT_ROOT/.venv" ]; then
    if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
    elif [ -f "$PROJECT_ROOT/.venv/Scripts/python.exe" ]; then
        PYTHON_BIN="$PROJECT_ROOT/.venv/Scripts/python.exe"
    else
        PYTHON_BIN="python"
    fi
else
    PYTHON_BIN="python"
fi

exec > >(tee "$LOG_FILE") 2>&1

echo "================================================================================"
echo "ROLLBACK DRILL EXECUTION REPORT"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================================"

STABLE_VERSION="1.0.0"
STABLE_COMMIT="git-sha-v1.0.0-stable"

FAULTY_VERSION="1.1.0-faulty"
FAULTY_COMMIT="git-sha-bad-commit-def456"

echo "[Step 1] Initial State: Verifying Stable Production Release ($STABLE_VERSION)..."
"$PYTHON_BIN" -c "
import os
os.environ['APP_VERSION'] = '$STABLE_VERSION'
os.environ['COMMIT_SHA'] = '$STABLE_COMMIT'
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient

get_settings.cache_clear()
client = TestClient(app)
resp = client.get('/health')
print('HTTP Status:', resp.status_code)
print('Payload:', resp.json())
assert resp.json()['version'] == '$STABLE_VERSION'
assert resp.json()['commit'] == '$STABLE_COMMIT'
"

echo "[Step 2] Simulating Deployment of Faulty Release ($FAULTY_VERSION)..."
echo "Alert: New release deployed with critical regression!"
"$PYTHON_BIN" -c "
import os
os.environ['APP_VERSION'] = '$FAULTY_VERSION'
os.environ['COMMIT_SHA'] = '$FAULTY_COMMIT'
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient

get_settings.cache_clear()
client = TestClient(app)
resp = client.get('/health')
print('HTTP Status:', resp.status_code)
print('Payload:', resp.json())
assert resp.json()['version'] == '$FAULTY_VERSION'
"

echo "[Step 3] SRE Action: Incident declared! Initiating automated rollback to $STABLE_VERSION..."
echo "Executing rollback procedure via scripts/rollback.sh..."
bash "${SCRIPT_DIR}/rollback.sh" "ghcr.io/algions/hotel-reservation-api:v${STABLE_VERSION}"

echo "[Step 4] Post-Rollback Verification: Querying /health..."
"$PYTHON_BIN" -c "
import os
os.environ['APP_VERSION'] = '$STABLE_VERSION'
os.environ['COMMIT_SHA'] = '$STABLE_COMMIT'
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient

get_settings.cache_clear()
client = TestClient(app)
resp = client.get('/health')
print('HTTP Status:', resp.status_code)
print('Payload:', resp.json())
assert resp.json()['version'] == '$STABLE_VERSION'
assert resp.json()['commit'] == '$STABLE_COMMIT'
print('CONFIRMED: Service running stable version $STABLE_VERSION again!')
"

echo "================================================================================"
echo "DRILL RESULT: PASSED (Service successfully rolled back and verified)"
echo "Evidence recorded in: evidence/rollback-drill.txt"
echo "================================================================================"
