"""Pydantic schemas for request validation and response serialization."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

CandidateStatus = Literal["applied", "screening", "interview", "offer", "hired", "rejected"]


class CandidateBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    skills: list[str] = Field(default_factory=list)
    experience: int = Field(default=0, ge=0)
    status: CandidateStatus = "applied"


class CandidateCreate(CandidateBase):
    """Payload used when creating a new candidate."""


class CandidateUpdate(BaseModel):
    """Payload used when updating an existing candidate."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    email: EmailStr | None = None
    skills: list[str] | None = None
    experience: int | None = Field(default=None, ge=0)
    status: CandidateStatus | None = None


class CandidateRead(CandidateBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
