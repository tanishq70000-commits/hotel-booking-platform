"""Main FastAPI application entry point with observability and reservation routes."""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import check_db_connection, get_db
from app.logging_config import setup_logging
from app.schemas import (
    HealthResponse,
    ReadyResponse,
    ReservationCreate,
    ReservationResponse,
    RoomResponse,
)
from app.services import (
    ReservationConflictError,
    RoomNotFoundError,
    RoomTypeNotFoundError,
    create_reservation,
    get_available_rooms,
    get_reservation_by_reference,
)
from app.ui import INDEX_HTML

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.VERSION} (commit: {settings.COMMIT_SHA}, env: {settings.APP_ENV})"
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade Hotel Reservation and Availability API",
    lifespan=lifespan,
)

# Instrument Prometheus metrics (/metrics)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:  # type: ignore
    """Middleware attaching request_id and emitting structured JSON access logs."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    status_code = 500
    response: Response | None = None

    try:
        response = await call_next(request)
        if response is not None:
            status_code = response.status_code
    except Exception as exc:
        status_code = 500
        logger.error(
            f"Unhandled server error: {exc}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
            },
        )
        raise exc from None
    finally:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if response is not None:
            response.headers["X-Request-ID"] = request_id
        # Skip logging noisy metrics polling
        if request.url.path != "/metrics":
            extra_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": latency_ms,
            }
            logger.info(
                f"{request.method} {request.url.path} -> {status_code} ({latency_ms}ms)",
                extra=extra_data,
            )

    assert response is not None
    return response


# --- Exception Handlers ---


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle 422 validation errors with clear error details."""
    errors = exc.errors()
    first_error = errors[0]["msg"] if errors else "Validation error"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": first_error, "errors": jsonable_encoder(errors)},
    )


@app.exception_handler(RoomNotFoundError)
async def room_not_found_handler(request: Request, exc: RoomNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(RoomTypeNotFoundError)
async def room_type_not_found_handler(request: Request, exc: RoomTypeNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(ReservationConflictError)
async def reservation_conflict_handler(
    request: Request, exc: ReservationConflictError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


# --- Web UI Portal Endpoint ---


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> HTMLResponse:
    """Hotel Reservation Web Portal landing page."""
    return HTMLResponse(content=INDEX_HTML)


# --- Health & Observability Endpoints ---


@app.get("/health", response_model=HealthResponse, tags=["Observability"])
def health() -> HealthResponse:
    """Liveness probe: returns healthy with build version and commit SHA."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        commit=settings.COMMIT_SHA,
    )


@app.get("/ready", response_model=ReadyResponse, tags=["Observability"])
def ready() -> ReadyResponse:
    """Readiness probe: verifies database reachability. Returns 503 if unavailable."""
    is_ready = check_db_connection()
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": "disconnected"},
        )
    return ReadyResponse(status="ready", database="connected")


# --- Reservation & Availability Business Endpoints ---


@app.get("/availability", response_model=list[RoomResponse], tags=["Availability"])
def check_availability(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    room_type: str = Query(..., description="Room type to query (e.g. single, double, suite)"),
    db: Session = Depends(get_db),
) -> list[RoomResponse]:
    """List available rooms of a given type for the specified date range.

    Validates:
    - check_out > check_in (422)
    - dates not in the past (422)
    - room_type exists (404)
    Allows back-to-back stays.
    """
    today = date.today()
    if check_in < today:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"check_in date ({check_in}) cannot be in the past",
        )
    if check_out <= check_in:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"check_out date ({check_out}) must be strictly after check_in ({check_in})",
        )

    rooms = get_available_rooms(db=db, check_in=check_in, check_out=check_out, room_type=room_type)
    return [RoomResponse.model_validate(r) for r in rooms]


@app.post(
    "/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reservations"],
)
def create_new_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
) -> ReservationResponse:
    """Create a confirmed reservation with concurrency safety.

    - Returns 201 Created with unique reference and status CONFIRMED
    - Returns 422 on invalid date range
    - Returns 404 on unknown room
    - Returns 409 on overlap (both application pre-check and PostgreSQL exclusion constraint)
    """
    reservation = create_reservation(db=db, payload=payload)
    return ReservationResponse.model_validate(reservation)


@app.get(
    "/reservations/{reference}",
    response_model=ReservationResponse,
    tags=["Reservations"],
)
def get_reservation(
    reference: str,
    db: Session = Depends(get_db),
) -> ReservationResponse:
    """Retrieve details for a single reservation by reference."""
    reservation = get_reservation_by_reference(db=db, reference=reference)
    return ReservationResponse.model_validate(reservation)
