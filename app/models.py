"""SQLAlchemy ORM models with PostgreSQL constraints."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class Room(Base):
    """Room model representing hotel inventory."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    room_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="room", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Room(id={self.id}, number='{self.number}', room_type='{self.room_type}')>"


class Reservation(Base):
    """Reservation model with strict PostgreSQL EXCLUDE constraint against double bookings."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    guest_name: Mapped[str] = mapped_column(String(128), nullable=False)
    guest_email: Mapped[str] = mapped_column(String(128), nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_out: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    room: Mapped["Room"] = relationship("Room", back_populates="reservations")

    __table_args__ = (
        CheckConstraint("check_out > check_in", name="check_valid_date_range"),
        # PostgreSQL GiST exclusion constraint: prevents overlapping CONFIRMED stays for the same room.
        # Uses half-open daterange '[)', allowing back-to-back stays where check_out = next check_in.
        ExcludeConstraint(  # type: ignore[no-untyped-call]
            ("room_id", "="),
            (func.daterange(check_in, check_out, "[)"), "&&"),
            where=(status == "CONFIRMED"),
            name="exclude_overlapping_confirmed_reservations",
            using="gist",
        ),
    )

    def __repr__(self) -> str:
        return f"<Reservation(id={self.id}, ref='{self.reference}', room_id={self.room_id}, status='{self.status}')>"


@event.listens_for(Reservation.__table__, "before_create")
def _strip_exclude_for_non_postgres(target, connection, **kw):  # type: ignore
    """Conditionally strip PostgreSQL-specific ExcludeConstraint when targeting non-PostgreSQL engines (e.g. SQLite in offline tests)."""
    if connection.dialect.name != "postgresql":
        exclude_constraints = [
            c for c in list(target.constraints) if isinstance(c, ExcludeConstraint)
        ]
        for c in exclude_constraints:
            target.constraints.remove(c)
