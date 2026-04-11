"""API integration tests for the candidate tracker."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"recruitment_test_{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    engine.dispose()
    TEST_DB_PATH.unlink(missing_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_candidate_crud_flow(client: TestClient):
    first_payload = {
        "name": "Ava Patel",
        "email": "ava.patel@example.com",
        "skills": ["Python", "FastAPI"],
        "experience": 5,
        "status": "screening",
    }
    second_payload = {
        "name": "Ben Carter",
        "email": "ben.carter@example.com",
        "skills": ["SQL"],
        "experience": 2,
        "status": "applied",
    }

    create_response = client.post("/api/v1/candidates/", json=first_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] > 0
    assert created["email"] == first_payload["email"]
    assert created["skills"] == first_payload["skills"]

    second_response = client.post("/api/v1/candidates/", json=second_payload)
    assert second_response.status_code == 201

    list_response = client.get("/api/v1/candidates/?name=ava")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.headers["X-Total-Count"] == "1"

    skill_response = client.get("/api/v1/candidates/?skill=Python")
    assert skill_response.status_code == 200
    assert len(skill_response.json()) == 1

    experience_response = client.get("/api/v1/candidates/?experience_min=4&experience_max=5")
    assert experience_response.status_code == 200
    assert len(experience_response.json()) == 1

    paged_response = client.get("/api/v1/candidates/?skip=0&limit=1&sort_by=name&sort_order=asc")
    assert paged_response.status_code == 200
    assert len(paged_response.json()) == 1
    assert paged_response.headers["X-Total-Count"] == "2"
    assert paged_response.json()[0]["name"] == "Ava Patel"

    second_page = client.get("/api/v1/candidates/?skip=1&limit=1&sort_by=name&sort_order=asc")
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1
    assert second_page.json()[0]["name"] == "Ben Carter"

    get_response = client.get(f"/api/v1/candidates/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Ava Patel"

    patch_response = client.patch(
        f"/api/v1/candidates/{created['id']}",
        json={"status": "interview"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "interview"
    assert patch_response.json()["experience"] == 5

    delete_response = client.delete(f"/api/v1/candidates/{created['id']}")
    assert delete_response.status_code == 204

    delete_second = client.delete(f"/api/v1/candidates/{second_response.json()['id']}")
    assert delete_second.status_code == 204

    missing_response = client.get(f"/api/v1/candidates/{created['id']}")
    assert missing_response.status_code == 404


def test_generated_docs_and_versions(client: TestClient):
    docs_response = client.get("/api/v1/system/generated-docs")
    assert docs_response.status_code == 200
    docs = docs_response.json()
    assert docs["info"]["title"] == "Recruitment Candidate Tracker API"
    assert "/api/v1/candidates" in docs["paths"]

    versions_response = client.get("/api/v1/system/versions")
    assert versions_response.status_code == 200
    assert isinstance(versions_response.json(), list)


def test_email_validation_and_conflict(client: TestClient):
    invalid_response = client.post(
        "/api/v1/candidates/",
        json={"name": "Broken", "email": "not-an-email", "skills": [], "experience": 0, "status": "applied"},
    )
    assert invalid_response.status_code == 422

    payload = {
        "name": "Sam Lee",
        "email": "sam.lee@example.com",
        "skills": ["SQL"],
        "experience": 2,
        "status": "applied",
    }
    first = client.post("/api/v1/candidates/", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/candidates/", json=payload)
    assert second.status_code == 409
