"""Business domain logic for room availability and reservations."""

import logging
import secrets
import threading
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Reservation, Room
from app.schemas import ReservationCreate

logger = logging.getLogger(__name__)

# Base32 alphabet (Crockford-style / RFC 4648 without ambiguous chars)
BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

_reservation_lock = threading.Lock()


class RoomNotFoundError(Exception):
    """Raised when a specified room ID is not found."""

    pass


class RoomTypeNotFoundError(Exception):
    """Raised when a requested room type does not exist in inventory."""

    pass


class ReservationConflictError(Exception):
    """Raised when an overlapping reservation exists for the requested room/dates (409 Conflict)."""

    pass


def generate_reservation_reference() -> str:
    """Generate a collision-resistant reservation reference (e.g. RSV-A1B2C3D4)."""
    random_chars = "".join(secrets.choice(BASE32_ALPHABET) for _ in range(8))
    return f"RSV-{random_chars}"


def get_available_rooms(db: Session, check_in: date, check_out: date, room_type: str) -> list[Room]:
    """Return all available rooms for a given room_type within [check_in, check_out).

    Allows back-to-back stays where previous check_out == current check_in.
    """
    # 1. Verify room_type exists in inventory
    type_exists = db.scalar(select(Room.id).where(Room.room_type == room_type).limit(1))
    if not type_exists:
        raise RoomTypeNotFoundError(f"Room type '{room_type}' does not exist")

    # 2. Find room IDs with overlapping CONFIRMED reservations
    # Two intervals [A_start, A_end) and [B_start, B_end) overlap iff:
    # A_start < B_end AND A_end > B_start.
    overlapping_subquery = (
        select(Reservation.room_id)
        .where(
            and_(
                Reservation.status == "CONFIRMED",
                Reservation.check_in < check_out,
                Reservation.check_out > check_in,
            )
        )
        .scalar_subquery()
    )

    # 3. Select rooms of requested type not in overlapping set
    stmt = (
        select(Room)
        .where(
            and_(
                Room.room_type == room_type,
                Room.id.not_in(overlapping_subquery),
            )
        )
        .order_by(Room.number)
    )
    return list(db.scalars(stmt).all())


def create_reservation(db: Session, payload: ReservationCreate) -> Reservation:
    """Create a confirmed reservation.

    Enforces concurrency safety at both the application level and the database level
    (PostgreSQL GiST EXCLUDE constraint). Overlapping requests result in ReservationConflictError (409).
    """
    with _reservation_lock:
        target_room_id: int | None = payload.room_id

        # If specific room_id was requested
        if target_room_id is not None:
            room = db.get(Room, target_room_id)
            if not room:
                raise RoomNotFoundError(f"Room with id {target_room_id} not found")
            if payload.room_type and room.room_type != payload.room_type:
                raise RoomNotFoundError(
                    f"Room {target_room_id} is of type '{room.room_type}', not '{payload.room_type}'"
                )

            # Pre-check for existing overlap
            conflict = db.scalar(
                select(Reservation.id)
                .where(
                    and_(
                        Reservation.room_id == target_room_id,
                        Reservation.status == "CONFIRMED",
                        Reservation.check_in < payload.check_out,
                        Reservation.check_out > payload.check_in,
                    )
                )
                .limit(1)
            )
            if conflict:
                raise ReservationConflictError(
                    f"Room {target_room_id} is already reserved for the requested dates"
                )
        else:
            # Assign an available room of the requested room_type
            assert payload.room_type is not None
            available_rooms = get_available_rooms(
                db=db,
                check_in=payload.check_in,
                check_out=payload.check_out,
                room_type=payload.room_type,
            )
            if not available_rooms:
                raise ReservationConflictError(
                    f"No available rooms of type '{payload.room_type}' for requested dates"
                )
            target_room_id = available_rooms[0].id

        # Create the reservation record
        max_retries = 3
        for attempt in range(max_retries):
            reference = generate_reservation_reference()
            reservation = Reservation(
                reference=reference,
                room_id=target_room_id,
                guest_name=payload.guest_name,
                guest_email=payload.guest_email,
                check_in=payload.check_in,
                check_out=payload.check_out,
                status="CONFIRMED",
            )
            db.add(reservation)

            try:
                db.commit()
                db.refresh(reservation)
                return reservation
            except IntegrityError as exc:
                db.rollback()
                orig_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
                # If the database exclusion constraint or overlap constraint was triggered
                if (
                    "exclude_overlapping" in orig_msg
                    or "exclusion" in orig_msg.lower()
                    or "conflict" in orig_msg.lower()
                ):
                    logger.warning(
                        f"Concurrency conflict: DB exclusion constraint caught double booking for room {target_room_id}"
                    )
                    raise ReservationConflictError(
                        f"Room {target_room_id} is already reserved for the requested dates"
                    ) from exc

                # If reference collision, retry with a fresh reference
                if "reference" in orig_msg and attempt < max_retries - 1:
                    logger.info("Reference collision detected, retrying with new reference...")
                    continue

                # Fallback check: treat other integrity errors on reservations as conflicts or re-raise
                raise ReservationConflictError(
                    f"Unable to confirm reservation due to conflict: {orig_msg}"
                ) from exc

        raise ReservationConflictError("Failed to generate a unique reservation reference")


def get_reservation_by_reference(db: Session, reference: str) -> Reservation:
    """Retrieve a single reservation by unique reference."""
    stmt = select(Reservation).where(Reservation.reference == reference)
    res = db.scalar(stmt)
    if not res:
        raise RoomNotFoundError(f"Reservation with reference '{reference}' not found")
    return res
