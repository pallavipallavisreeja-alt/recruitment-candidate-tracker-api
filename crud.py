"""Database access helpers for candidate records."""

from __future__ import annotations

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas


class CandidateNotFoundError(LookupError):
    """Raised when a candidate cannot be located."""


class DuplicateCandidateError(ValueError):
    """Raised when a unique constraint would be violated."""


def _candidate_query(db: Session):
    return db.query(models.Candidate)


def _sort_expression(sort_by: str, sort_order: str):
    sort_columns = {
        "created_at": models.Candidate.created_at,
        "name": models.Candidate.name,
        "experience": models.Candidate.experience,
        "status": models.Candidate.status,
    }
    column = sort_columns.get(sort_by, models.Candidate.created_at)
    return desc(column) if sort_order.lower() == "desc" else asc(column)


def get_candidate_by_id(db: Session, candidate_id: int) -> models.Candidate:
    candidate = _candidate_query(db).filter(models.Candidate.id == candidate_id).first()
    if candidate is None:
        raise CandidateNotFoundError(f"Candidate {candidate_id} not found")
    return candidate


def get_candidate_by_email(db: Session, email: str) -> models.Candidate | None:
    normalized_email = email.strip().lower()
    return _candidate_query(db).filter(func.lower(models.Candidate.email) == normalized_email).first()


def create_candidate(db: Session, candidate: schemas.CandidateCreate) -> models.Candidate:
    normalized_email = candidate.email.strip().lower()
    normalized_name = candidate.name.strip()

    if get_candidate_by_email(db, normalized_email):
        raise DuplicateCandidateError("Candidate email already exists")

    db_candidate = models.Candidate(
        name=normalized_name,
        email=normalized_email,
        experience=candidate.experience,
        status=candidate.status,
    )
    db_candidate.skills = candidate.skills

    db.add(db_candidate)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCandidateError("Candidate email already exists") from exc

    db.refresh(db_candidate)
    return db_candidate


def list_candidates(
    db: Session,
    name: str | None = None,
    status: str | None = None,
    skill: str | None = None,
    experience_min: int | None = None,
    experience_max: int | None = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[models.Candidate], int]:
    query = _candidate_query(db)
    if name:
        query = query.filter(models.Candidate.name.ilike(f"%{name.strip()}%"))
    if status:
        query = query.filter(models.Candidate.status == status)
    if skill:
        query = query.filter(models.Candidate._skills.ilike(f"%{skill.strip()}%"))
    if experience_min is not None:
        query = query.filter(models.Candidate.experience >= experience_min)
    if experience_max is not None:
        query = query.filter(models.Candidate.experience <= experience_max)

    total = query.count()
    items = (
        query.order_by(_sort_expression(sort_by, sort_order))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_candidate(
    db: Session,
    candidate_id: int,
    candidate_data: schemas.CandidateUpdate,
) -> models.Candidate:
    candidate = get_candidate_by_id(db, candidate_id)
    data = candidate_data.model_dump(exclude_unset=True)

    if "email" in data and data["email"]:
        normalized_email = data["email"].strip().lower()
        if normalized_email != candidate.email.strip().lower() and get_candidate_by_email(db, normalized_email):
            raise DuplicateCandidateError("Candidate email already exists")

    for key, value in data.items():
        if key == "skills":
            candidate.skills = value
        elif key == "email" and value:
            setattr(candidate, key, value.strip().lower())
        elif key == "name" and value:
            setattr(candidate, key, value.strip())
        elif value is not None:
            setattr(candidate, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCandidateError("Candidate email already exists") from exc

    db.refresh(candidate)
    return candidate


def delete_candidate(db: Session, candidate_id: int) -> models.Candidate:
    candidate = get_candidate_by_id(db, candidate_id)
    db.delete(candidate)
    db.commit()
    return candidate
