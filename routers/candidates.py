"""Candidate API routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status as http_status
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db

# ✅ Router must be defined first
router = APIRouter(prefix="/api/v1/candidates", tags=["Candidates"])


@router.post(
    "/",
    response_model=schemas.CandidateRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a candidate",
)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_candidate(db, candidate)
    except crud.DuplicateCandidateError as exc:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/", response_model=list[schemas.CandidateRead], summary="List candidates")
def get_candidates(
    response: Response,
    name: str | None = Query(default=None, description="Case-insensitive candidate name filter"),
    status: schemas.CandidateStatus | None = Query(default=None, description="Filter by candidate status"),
    skill: str | None = Query(default=None, description="Filter by skill substring"),
    experience_min: int | None = Query(default=None, ge=0, description="Minimum years of experience"),
    experience_max: int | None = Query(default=None, ge=0, description="Maximum years of experience"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum records to return"),
    sort_by: Literal["created_at", "name", "experience", "status"] = Query(
        default="created_at", description="Sort field"
    ),
    sort_order: Literal["asc", "desc"] = Query(default="desc", description="Sort direction"),
    db: Session = Depends(get_db),
):
    items, total = crud.list_candidates(
        db,
        name=name,
        status=status,
        skill=skill,
        experience_min=experience_min,
        experience_max=experience_max,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{candidate_id}", response_model=schemas.CandidateRead, summary="Get candidate")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_candidate_by_id(db, candidate_id)
    except crud.CandidateNotFoundError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{candidate_id}", response_model=schemas.CandidateRead, summary="Update candidate")
def update_candidate(candidate_id: int, candidate: schemas.CandidateUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_candidate(db, candidate_id, candidate)
    except crud.CandidateNotFoundError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except crud.DuplicateCandidateError as exc:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{candidate_id}", status_code=http_status.HTTP_204_NO_CONTENT, summary="Delete candidate")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_candidate(db, candidate_id)
    except crud.CandidateNotFoundError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc