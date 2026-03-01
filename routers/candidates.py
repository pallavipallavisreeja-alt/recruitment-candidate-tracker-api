from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas
from database import SessionLocal

router = APIRouter(
    prefix="/api/v1/candidates",
    tags=["Candidates"]
)

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# POST - Create Candidate
@router.post(
    "/",
    response_model=schemas.CandidateResponse,
    summary="Create a new candidate",
    description="This API creates a new candidate and stores it in the database."
)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(get_db)):
    return crud.create_candidate(db, candidate)


# GET - All Candidates
from typing import Optional, List
@router.get("/", response_model=List[schemas.CandidateResponse])
def get_candidates(name: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_all_candidates(db, name)


# GET - Single Candidate
@router.get("/{candidate_id}", response_model=schemas.CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = crud.get_candidate_by_id(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


# PUT - Update Candidate
@router.put("/{candidate_id}", response_model=schemas.CandidateResponse)
def update_candidate(candidate_id: int, candidate: schemas.CandidateCreate, db: Session = Depends(get_db)):
    updated_candidate = crud.update_candidate(db, candidate_id, candidate)
    if not updated_candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated_candidate


# DELETE - Remove Candidate
@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = crud.delete_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully"}