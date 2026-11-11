"""Comprehensive tests for reservation creation, fetching, and overlap constraints."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.models import Room


def test_create_reservation_by_room_id(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test successful reservation creation with room_id."""
    today = date.today()
    target_room = sample_rooms[0]

    payload = {
        "guest_name": "Jane Doe",
        "guest_email": "jane.doe@example.com",
        "room_id": target_room.id,
        "check_in": str(today + timedelta(days=5)),
        "check_out": str(today + timedelta(days=9)),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["reference"].startswith("RSV-")
    assert len(data["reference"]) == 12  # RSV- (4) + 8 chars
    assert data["room_id"] == target_room.id
    assert data["status"] == "CONFIRMED"
    assert data["guest_name"] == "Jane Doe"


def test_create_reservation_by_room_type(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test reservation creation specifying room_type instead of room_id."""
    today = date.today()
    payload = {
        "guest_name": "Alex Smith",
        "guest_email": "alex@example.com",
        "room_type": "suite",
        "check_in": str(today + timedelta(days=5)),
        "check_out": str(today + timedelta(days=8)),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["reference"].startswith("RSV-")
    assert data["status"] == "CONFIRMED"


def test_create_reservation_unknown_room_id(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test 404 when requested room ID does not exist."""
    today = date.today()
    payload = {
        "guest_name": "Jane Doe",
        "guest_email": "jane@example.com",
        "room_id": 999999,
        "check_in": str(today + timedelta(days=5)),
        "check_out": str(today + timedelta(days=9)),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 404


def test_create_reservation_invalid_dates(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test 422 when dates are invalid."""
    today = date.today()
    target_room = sample_rooms[0]

    # Check-out before check-in
    payload = {
        "guest_name": "Invalid Dates",
        "guest_email": "invalid@example.com",
        "room_id": target_room.id,
        "check_in": str(today + timedelta(days=10)),
        "check_out": str(today + timedelta(days=8)),
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 422


def test_back_to_back_reservations_allowed(client: TestClient, sample_rooms: list[Room]) -> None:
    """Back-to-back stays (checkout day = next check-in day) must be allowed."""
    today = date.today()
    target_room = sample_rooms[0]

    # First stay: days 10 -> 15
    resp1 = client.post(
        "/reservations",
        json={
            "guest_name": "Guest One",
            "guest_email": "g1@example.com",
            "room_id": target_room.id,
            "check_in": str(today + timedelta(days=10)),
            "check_out": str(today + timedelta(days=15)),
        },
    )
    assert resp1.status_code == 201

    # Second stay: days 15 -> 20 (back-to-back on same room!)
    resp2 = client.post(
        "/reservations",
        json={
            "guest_name": "Guest Two",
            "guest_email": "g2@example.com",
            "room_id": target_room.id,
            "check_in": str(today + timedelta(days=15)),
            "check_out": str(today + timedelta(days=20)),
        },
    )
    assert resp2.status_code == 201


def test_overlapping_reservations_rejected_all_cases(
    client: TestClient, sample_rooms: list[Room]
) -> None:
    """All variations of overlapping date ranges must return 409 Conflict."""
    today = date.today()
    target_room = sample_rooms[0]

    # Base reservation: days 10 -> 20
    base_resp = client.post(
        "/reservations",
        json={
            "guest_name": "Base Guest",
            "guest_email": "base@example.com",
            "room_id": target_room.id,
            "check_in": str(today + timedelta(days=10)),
            "check_out": str(today + timedelta(days=20)),
        },
    )
    assert base_resp.status_code == 201

    conflict_cases = [
        ("exact", today + timedelta(days=10), today + timedelta(days=20)),
        ("partial_start", today + timedelta(days=8), today + timedelta(days=15)),
        ("partial_end", today + timedelta(days=15), today + timedelta(days=25)),
        ("contained", today + timedelta(days=12), today + timedelta(days=18)),
        ("containing", today + timedelta(days=8), today + timedelta(days=25)),
    ]

    for label, c_in, c_out in conflict_cases:
        resp = client.post(
            "/reservations",
            json={
                "guest_name": f"Conflicting Guest {label}",
                "guest_email": f"conflict_{label}@example.com",
                "room_id": target_room.id,
                "check_in": str(c_in),
                "check_out": str(c_out),
            },
        )
        assert (
            resp.status_code == 409
        ), f"Failed for case {label}: expected 409, got {resp.status_code}"


def test_get_reservation_by_reference(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test retrieving an existing reservation by reference."""
    today = date.today()
    create_resp = client.post(
        "/reservations",
        json={
            "guest_name": "Fetch Me",
            "guest_email": "fetch@example.com",
            "room_id": sample_rooms[0].id,
            "check_in": str(today + timedelta(days=30)),
            "check_out": str(today + timedelta(days=35)),
        },
    )
    assert create_resp.status_code == 201
    ref = create_resp.json()["reference"]

    get_resp = client.get(f"/reservations/{ref}")
    assert get_resp.status_code == 200
    assert get_resp.json()["reference"] == ref
    assert get_resp.json()["guest_name"] == "Fetch Me"


def test_get_reservation_not_found(client: TestClient) -> None:
    """Test 404 when fetching non-existent reservation reference."""
    response = client.get("/reservations/RSV-NONEXISTENT")
    assert response.status_code == 404
