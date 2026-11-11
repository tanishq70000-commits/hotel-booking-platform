"""Repeatable, idempotent database seed script."""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Reservation, Room

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

ROOMS_DATA: list[tuple[str, str, Decimal]] = [
    ("101", "single", Decimal("89.00")),
    ("102", "single", Decimal("89.00")),
    ("103", "single", Decimal("99.00")),
    ("201", "double", Decimal("129.00")),
    ("202", "double", Decimal("129.00")),
    ("203", "double", Decimal("139.00")),
    ("204", "double", Decimal("149.00")),
    ("301", "suite", Decimal("249.00")),
    ("302", "suite", Decimal("279.00")),
    ("303", "deluxe-suite", Decimal("349.00")),
]


def seed_database() -> None:
    """Populate inventory and initial sample reservations idempotently."""
    logger.info("Starting database seeding...")
    db: Session = SessionLocal()

    try:
        # 1. Seed Rooms
        rooms_added = 0
        for number, room_type, price in ROOMS_DATA:
            existing = db.scalar(select(Room).where(Room.number == number))
            if not existing:
                room = Room(number=number, room_type=room_type, price=price)
                db.add(room)
                rooms_added += 1

        db.commit()
        logger.info(f"Rooms seeding completed. Added {rooms_added} new rooms.")

        # 2. Seed Sample Reservations
        today = date.today()
        sample_reservations = [
            {
                "reference": "RSV-SEED0001",
                "room_number": "101",
                "guest_name": "Alice Smith",
                "guest_email": "alice.smith@example.com",
                "check_in": today + timedelta(days=10),
                "check_out": today + timedelta(days=14),
            },
            {
                "reference": "RSV-SEED0002",
                "room_number": "201",
                "guest_name": "Bob Jones",
                "guest_email": "bob.jones@example.com",
                "check_in": today + timedelta(days=15),
                "check_out": today + timedelta(days=18),
            },
        ]

        reservations_added = 0
        for r_data in sample_reservations:
            existing_res = db.scalar(
                select(Reservation).where(Reservation.reference == r_data["reference"])
            )
            if not existing_res:
                target_room: Room | None = db.scalar(
                    select(Room).where(Room.number == r_data["room_number"])
                )
                if target_room:
                    res = Reservation(
                        reference=r_data["reference"],
                        room_id=target_room.id,
                        guest_name=r_data["guest_name"],
                        guest_email=r_data["guest_email"],
                        check_in=r_data["check_in"],
                        check_out=r_data["check_out"],
                        status="CONFIRMED",
                    )
                    db.add(res)
                    reservations_added += 1

        db.commit()
        logger.info(f"Sample reservations seeded. Added {reservations_added} new reservations.")

        total_rooms = db.query(Room).count()
        total_reservations = db.query(Reservation).count()
        logger.info(
            f"Seeding finished successfully. Current state: {total_rooms} rooms, {total_reservations} reservations."
        )

    except Exception as exc:
        db.rollback()
        logger.error(f"Seeding failed: {exc}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
