"""Tests for the /availability endpoint."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.models import Room


def test_availability_success(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test querying availability for a valid future date range and existing room type."""
    today = date.today()
    check_in = today + timedelta(days=10)
    check_out = today + timedelta(days=15)

    response = client.get(
        f"/availability?check_in={check_in}&check_out={check_out}&room_type=single"
    )
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) == 2  # rooms 101 and 102
    assert all(r["room_type"] == "single" for r in rooms)


def test_availability_invalid_dates_checkout_before_checkin(
    client: TestClient, sample_rooms: list[Room]
) -> None:
    """Test 422 error when check_out <= check_in."""
    today = date.today()
    check_in = today + timedelta(days=10)
    check_out = today + timedelta(days=5)

    response = client.get(
        f"/availability?check_in={check_in}&check_out={check_out}&room_type=single"
    )
    assert response.status_code == 422
    assert "strictly after check_in" in response.text


def test_availability_same_day_checkout(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test 422 error when check_in == check_out (zero nights)."""
    today = date.today()
    check_in = today + timedelta(days=10)

    response = client.get(
        f"/availability?check_in={check_in}&check_out={check_in}&room_type=single"
    )
    assert response.status_code == 422


def test_availability_past_dates(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test 422 error when check_in is in the past."""
    past_date = date.today() - timedelta(days=2)
    check_out = date.today() + timedelta(days=3)

    response = client.get(
        f"/availability?check_in={past_date}&check_out={check_out}&room_type=single"
    )
    assert response.status_code == 422
    assert "cannot be in the past" in response.text


def test_availability_unknown_room_type(client: TestClient, sample_rooms: list[Room]) -> None:
    """Test 404 error when room_type does not exist in inventory."""
    today = date.today()
    check_in = today + timedelta(days=10)
    check_out = today + timedelta(days=12)

    response = client.get(
        f"/availability?check_in={check_in}&check_out={check_out}&room_type=presidential_penthouse"
    )
    assert response.status_code == 404
    assert "does not exist" in response.text


def test_availability_excludes_booked_rooms_allows_back_to_back(
    client: TestClient, sample_rooms: list[Room]
) -> None:
    """Test that booked rooms are excluded during booked range, but available back-to-back."""
    today = date.today()
    # Book room 101 from days +10 to +15
    res_resp = client.post(
        "/reservations",
        json={
            "guest_name": "Test Guest",
            "guest_email": "guest@example.com",
            "room_id": sample_rooms[0].id,  # 101
            "check_in": str(today + timedelta(days=10)),
            "check_out": str(today + timedelta(days=15)),
        },
    )
    assert res_resp.status_code == 201

    # Query for overlapping range (days 12 to 14) -> room 101 must NOT appear
    avail_overlap = client.get(
        f"/availability?check_in={today + timedelta(days=12)}&check_out={today + timedelta(days=14)}&room_type=single"
    )
    assert avail_overlap.status_code == 200
    overlap_rooms = avail_overlap.json()
    assert len(overlap_rooms) == 1
    assert overlap_rooms[0]["number"] == "102"

    # Query for back-to-back stay starting on day 15 (check_in = day 15) -> room 101 MUST be available!
    avail_b2b = client.get(
        f"/availability?check_in={today + timedelta(days=15)}&check_out={today + timedelta(days=20)}&room_type=single"
    )
    assert avail_b2b.status_code == 200
    b2b_room_numbers = [r["number"] for r in avail_b2b.json()]
    assert "101" in b2b_room_numbers
    assert "102" in b2b_room_numbers
