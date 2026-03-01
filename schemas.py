from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    skills: Optional[str] = None
    experience_years: Optional[int] = None
    status: Optional[str] = "Applied"

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True