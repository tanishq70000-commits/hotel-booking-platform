"""Pydantic v2 schemas for request validation and response serialization."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class HealthResponse(BaseModel):
    """Health / liveness probe response."""

    status: str = "healthy"
    version: str
    commit: str


class ReadyResponse(BaseModel):
    """Readiness probe response indicating dependency health."""

    status: str = "ready"
    database: str = "connected"


class RoomBase(BaseModel):
    """Base schema for Room."""

    number: str
    room_type: str
    price: Decimal


class RoomResponse(RoomBase):
    """Room response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class ReservationCreate(BaseModel):
    """Payload to create a new reservation."""

    guest_name: str = Field(..., min_length=2, max_length=128, description="Guest full name")
    guest_email: EmailStr = Field(..., description="Guest contact email")
    room_id: int | None = Field(default=None, description="Specific room ID to reserve")
    room_type: str | None = Field(
        default=None, description="Desired room type if room_id is not specified"
    )
    check_in: date = Field(..., description="Check-in date (inclusive)")
    check_out: date = Field(..., description="Check-out date (exclusive)")

    @model_validator(mode="after")
    def validate_reservation_dates_and_target(self) -> "ReservationCreate":
        today = date.today()
        if self.check_in < today:
            raise ValueError(f"check_in date ({self.check_in}) cannot be in the past")
        if self.check_out <= self.check_in:
            raise ValueError(
                f"check_out date ({self.check_out}) must be strictly after check_in ({self.check_in})"
            )
        if self.room_id is None and not self.room_type:
            raise ValueError("Either 'room_id' or 'room_type' must be provided")
        return self


class ReservationResponse(BaseModel):
    """Reservation confirmation response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    status: str
    created_at: datetime
    room: RoomResponse | None = None
