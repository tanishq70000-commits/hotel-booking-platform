#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Concurrency Demo Script
# Fires N simultaneous conflicting reservation requests for the exact same
# room and date range against the reservation service.
# Proves: Exactly ONE confirmed reservation (201) and ALL others rejected (409).
# Saves output to evidence/concurrency-demo.txt.
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EVIDENCE_DIR="${PROJECT_ROOT}/evidence"
mkdir -p "$EVIDENCE_DIR"
LOG_FILE="${EVIDENCE_DIR}/concurrency-demo.txt"

exec > >(tee "$LOG_FILE") 2>&1

echo "================================================================================"
echo "CONCURRENCY RACE CONDITION ACCEPTANCE DEMO"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================================================================"

# Execute the concurrency verification runner
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
"$PYTHON_BIN" -u -c "
import os
import concurrent.futures
from datetime import date, timedelta
from app.config import get_settings

# Use SQLite fallback if no external PostgreSQL URL provided
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:///test_hotel_booking.db'
get_settings.cache_clear()

from app.database import SessionLocal, engine
from app.models import Base, Room, Reservation
from fastapi.testclient import TestClient
from app.main import app

Base.metadata.create_all(bind=engine)

# Ensure room 101 exists
db = SessionLocal()
room = db.query(Room).filter_by(number='101').first()
if not room:
    room = Room(number='101', room_type='single', price=99.00)
    db.add(room)
    db.commit()
    db.refresh(room)

room_id = room.id
today = date.today()
check_in = str(today + timedelta(days=40))
check_out = str(today + timedelta(days=45))

# Purge any pre-existing reservations for this test window
db.query(Reservation).filter(
    Reservation.room_id == room_id,
    Reservation.check_in == check_in
).delete()
db.commit()
db.close()

client = TestClient(app)
NUM_REQUESTS = 10
print(f'Firing {NUM_REQUESTS} concurrent conflicting reservation requests for Room {room_id} ({check_in} -> {check_out})...')

def send_req(i):
    payload = {
        'guest_name': f'Demo Guest {i+1}',
        'guest_email': f'demo{i+1}@example.com',
        'room_id': room_id,
        'check_in': check_in,
        'check_out': check_out
    }
    resp = client.post('/reservations', json=payload)
    return resp.status_code, resp.json()

with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_REQUESTS) as ex:
    futures = [ex.submit(send_req, i) for i in range(NUM_REQUESTS)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

print('\n--- Results Summary ---')
successes = [r for r in results if r[0] == 201]
conflicts = [r for r in results if r[0] == 409]

for code, data in results:
    if code == 201:
        print(f'-> HTTP {code} CREATED   | Reference: {data.get(\"reference\")} | Guest: {data.get(\"guest_name\")}')
    else:
        print(f'-> HTTP {code} CONFLICT  | Detail: {data.get(\"detail\")}')

print(f'\nTotal Requests: {NUM_REQUESTS}')
print(f'Success Count (201 Created):  {len(successes)}')
print(f'Conflict Count (409 Conflict): {len(conflicts)}')

assert len(successes) == 1, f'Expected exactly 1 success, got {len(successes)}'
assert len(conflicts) == NUM_REQUESTS - 1, f'Expected {NUM_REQUESTS - 1} conflicts, got {len(conflicts)}'
print('\n[VERIFIED] Concurrency protection succeeded: exactly 1 booking confirmed, 9 rejected with 409.')
"

echo "================================================================================"
echo "DEMO EXECUTION COMPLETE"
echo "Saved audit log to: evidence/concurrency-demo.txt"
echo "================================================================================"
