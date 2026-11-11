"""Pytest fixtures for API and database tests."""

import os
from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.database import get_db
from app.main import app
from app.models import Base, Room

# Check for real PostgreSQL test database URL; fallback to file-based SQLite with WAL mode for concurrency
TEST_DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not TEST_DB_URL or "postgresql" not in TEST_DB_URL:
    SQLITE_PATH = os.path.abspath("test_hotel_booking.db")
    TEST_DB_URL = f"sqlite:///{SQLITE_PATH}"
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )
else:
    SQLITE_PATH = None
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database_schema() -> Generator[None, None, None]:
    """Create all database tables once for the test session."""
    if SQLITE_PATH:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA busy_timeout=10000;"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if SQLITE_PATH and os.path.exists(SQLITE_PATH):
        try:
            os.remove(SQLITE_PATH)
        except OSError:
            pass
        for extra in [f"{SQLITE_PATH}-wal", f"{SQLITE_PATH}-shm"]:
            if os.path.exists(extra):
                try:
                    os.remove(extra)
                except OSError:
                    pass


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session rolled back or cleared after each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Clean tables between tests
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Test client with overridden get_db dependency creating a fresh session per request."""

    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_rooms(db_session: Session) -> list[Room]:
    """Seed a standard set of rooms for tests."""
    rooms = [
        Room(number="101", room_type="single", price=Decimal("80.00")),
        Room(number="102", room_type="single", price=Decimal("85.00")),
        Room(number="201", room_type="double", price=Decimal("120.00")),
        Room(number="202", room_type="double", price=Decimal("130.00")),
        Room(number="301", room_type="suite", price=Decimal("250.00")),
    ]
    db_session.add_all(rooms)
    db_session.commit()
    for r in rooms:
        db_session.refresh(r)
    return rooms
