from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    skills = Column(String)
    experience_years = Column(Integer)
    status = Column(String, default="Applied")
    created_at = Column(DateTime, default=datetime.utcnow)