"""Database configuration and session helpers."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BASE_DIR / "recruitment_app.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")


def _build_engine(database_url: str):
    if not database_url.startswith("sqlite"):
        return create_engine(database_url, future=True)

    if database_url == f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}":
        try:
            DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            probe = sqlite3.connect(DEFAULT_SQLITE_PATH)
            probe.execute("CREATE TABLE IF NOT EXISTS __db_probe (id INTEGER PRIMARY KEY)")
            probe.execute("DROP TABLE IF EXISTS __db_probe")
            probe.commit()
            probe.close()
        except Exception:
            return create_engine(
                "sqlite://",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                future=True,
            )

    return create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )


engine = _build_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator:
    """Yield a short-lived database session for request handling."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_candidate_schema() -> None:
    """Bring older SQLite databases up to the current candidate schema."""

    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if not inspector.has_table("candidates"):
        return

    columns = {column["name"] for column in inspector.get_columns("candidates")}

    with engine.begin() as connection:
        if "experience" not in columns:
            connection.execute(text("ALTER TABLE candidates ADD COLUMN experience INTEGER NOT NULL DEFAULT 0"))
            if "experience_years" in columns:
                connection.execute(text("UPDATE candidates SET experience = COALESCE(experience_years, 0)"))

        if "skills" in columns and "_skills" in columns:
            # No-op for safety; older scratch tables from earlier experiments may already be normalized.
            pass
