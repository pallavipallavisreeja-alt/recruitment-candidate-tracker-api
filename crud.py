from sqlalchemy.orm import Session
import models, schemas

def create_candidate(db: Session, candidate: schemas.CandidateCreate):
    db_candidate = models.Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def get_all_candidates(db: Session, name: str = None):
    query = db.query(models.Candidate)

    if name:
        query = query.filter(models.Candidate.name.ilike(f"%{name}%"))

    return query.all()

def get_candidate_by_id(db: Session, candidate_id: int):
    return db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()

def update_candidate(db: Session, candidate_id: int, candidate_data: schemas.CandidateCreate):
    candidate = get_candidate_by_id(db, candidate_id)
    if candidate:
        for key, value in candidate_data.dict().items():
            setattr(candidate, key, value)
        db.commit()
        db.refresh(candidate)
    return candidate

def delete_candidate(db: Session, candidate_id: int):
    candidate = get_candidate_by_id(db, candidate_id)
    if candidate:
        db.delete(candidate)
        db.commit()
    return candidate