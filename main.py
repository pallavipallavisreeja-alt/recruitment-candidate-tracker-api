from fastapi import FastAPI, HTTPException
from typing import List
from models import Candidate   # import from your models.py

app = FastAPI()

# In-memory data
SAMPLE_CANDIDATES = [
    {
        "candidate_id": "C002",
        "name": "Ravi Teja",
        "email": "raviteja02@example.com",
        "skills": ["Python", "FastAPI", "SQL"],
        "experience_years": 3,
        "status": "Applied"
    },
    {
        "candidate_id": "C004",
        "name": "Harini dev",
        "email": "harinid04@example.com",
        "skills": ["JavaScript", "React", "Node.js"],
        "experience_years": 5,
        "status": "Interviewed"
    },
    {
        "candidate_id": "C006",
        "name": "Krupa Raj",
        "email": "kruparaj06@example.com",
        "skills": ["Java", "Spring Boot"],
        "experience_years": 4,
        "status": "Hired"
    }
]


# ---------------- CREATE ----------------
@app.post("/candidates/", response_model=Candidate)
def create_candidate(candidate: Candidate):
    for c in SAMPLE_CANDIDATES:
        if c["candidate_id"] == candidate.candidate_id:
            raise HTTPException(status_code=400, detail="Candidate already exists")
    SAMPLE_CANDIDATES.append(candidate.dict())
    return candidate


# ---------------- READ ALL ----------------
@app.get("/candidates/", response_model=List[Candidate])
def get_all_candidates():
    return SAMPLE_CANDIDATES


# ---------------- READ ONE ----------------
@app.get("/candidates/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str):
    for c in SAMPLE_CANDIDATES:
        if c["candidate_id"] == candidate_id:
            return c
    raise HTTPException(status_code=404, detail="Candidate not found")


# ---------------- UPDATE ----------------
@app.put("/candidates/{candidate_id}", response_model=Candidate)
def update_candidate(candidate_id: str, updated_candidate: Candidate):
    for index, c in enumerate(SAMPLE_CANDIDATES):
        if c["candidate_id"] == candidate_id:
            SAMPLE_CANDIDATES[index] = updated_candidate.dict()
            return updated_candidate
    raise HTTPException(status_code=404, detail="Candidate not found")


# ---------------- DELETE ----------------
@app.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: str):
    for index, c in enumerate(SAMPLE_CANDIDATES):
        if c["candidate_id"] == candidate_id:
            SAMPLE_CANDIDATES.pop(index)
            return {"message": "Candidate deleted successfully"}
    raise HTTPException(status_code=404, detail="Candidate not found")