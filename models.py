from pydantic import BaseModel, EmailStr
from typing import List

class Candidate(BaseModel):
    candidate_id: str
    name: str
    email: EmailStr
    skills: List[str]
    experience_years: int
    status: str

SAMPLE_CANDIDATES= [
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