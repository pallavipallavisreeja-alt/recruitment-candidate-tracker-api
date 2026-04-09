"""SQLAlchemy models for candidate storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class Candidate(Base):
    """Persistent candidate record."""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    _skills = Column("skills", Text, nullable=False, default="[]")
    experience = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="applied", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    @property
    def skills(self) -> list[str]:
        try:
            return json.loads(self._skills or "[]")
        except json.JSONDecodeError:
            return []

    @skills.setter
    def skills(self, value: list[str] | str | None) -> None:
        if value is None:
            self._skills = "[]"
        elif isinstance(value, str):
            self._skills = json.dumps([item.strip() for item in value.split(",") if item.strip()])
        else:
            self._skills = json.dumps(value)
