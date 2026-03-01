from fastapi import FastAPI
from database import engine, Base
from routers import candidates

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recruitment Candidate Tracker API",
    description="Intelligent API Documentation Keeper Demo",
    version="1.0.0"
)

app.include_router(candidates.router)