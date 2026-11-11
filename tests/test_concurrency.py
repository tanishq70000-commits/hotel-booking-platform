"""Concurrency acceptance test: fire N>=10 simultaneous conflicting POSTs."""

import concurrent.futures
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Reservation, Room


def test_concurrent_conflicting_reservations_exactly_one_wins(
    client: TestClient, db_session: Session, sample_rooms: list[Room]
) -> None:
    """Acceptance test #1: Fire N>=10 simultaneous conflicting POSTs for the exact same room and dates.

    Assert:
    - Exactly one request returns HTTP 201 Created.
    - All other (N-1) requests return HTTP 409 Conflict.
    - Exactly one reservation record is committed to the database.
    """
    target_room = sample_rooms[0]
    today = date.today()
    check_in = str(today + timedelta(days=20))
    check_out = str(today + timedelta(days=25))

    num_concurrent_requests = 12

    def fire_reservation_request(idx: int) -> tuple[int, dict]:
        payload = {
            "guest_name": f"Concurrent Guest {idx}",
            "guest_email": f"guest{idx}@example.com",
            "room_id": target_room.id,
            "check_in": check_in,
            "check_out": check_out,
        }
        resp = client.post("/reservations", json=payload)
        return resp.status_code, resp.json()

    # Fire N requests simultaneously using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
        futures = [
            executor.submit(fire_reservation_request, i) for i in range(num_concurrent_requests)
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    status_codes = [status for status, _ in results]
    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)

    # Acceptance assertions
    assert (
        success_count == 1
    ), f"Expected exactly 1 success (201), got {success_count}. Status codes: {status_codes}"
    assert (
        conflict_count == num_concurrent_requests - 1
    ), f"Expected {num_concurrent_requests - 1} conflicts (409), got {conflict_count}. Status codes: {status_codes}"

    # Verify database state has exactly one row
    confirmed_rows = list(
        db_session.scalars(
            select(Reservation).where(
                Reservation.room_id == target_room.id,
                Reservation.status == "CONFIRMED",
            )
        ).all()
    )
    assert (
        len(confirmed_rows) == 1
    ), f"Database must contain exactly 1 confirmed reservation, found {len(confirmed_rows)}"
