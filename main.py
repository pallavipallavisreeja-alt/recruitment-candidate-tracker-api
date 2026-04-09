"""Application entrypoint for the Recruitment Candidate Tracker API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, ensure_candidate_schema, engine
from routers.candidates import router as candidates_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("recruitment_tracker")


def create_app() -> FastAPI:
    """Build the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=engine)
        ensure_candidate_schema()
        logger.info("Database schema initialized")
        yield

    app = FastAPI(
        title="Recruitment Candidate Tracker API",
        description="Intelligent API Documentation Keeper for candidate operations.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(candidates_router)
    return app


app = create_app()
