"""Vercel Serverless Function entry point for FastAPI."""

import os
import sys

# Ensure root workspace is in Python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# If no cloud database is specified, use ephemeral SQLite in /tmp for serverless runtime
if not os.environ.get("DATABASE_URL") and not os.environ.get("DB_HOST"):
    os.environ["DATABASE_URL"] = "sqlite:////tmp/hotel_booking.db"

# Auto-initialize database tables and seed inventory if needed
try:
    from sqlalchemy import func, select

    from app.database import SessionLocal, engine
    from app.models import Base, Room
    from scripts.seed import seed_database

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db_session:
        count = db_session.scalar(select(func.count(Room.id)))
        if not count:
            seed_database()
except Exception:
    pass

from app.main import app  # noqa: E402

__all__ = ["app"]
