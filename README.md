# Intelligent API Documentation Keeper

Recruitment Candidate Tracker API built with FastAPI, SQLAlchemy, and Pydantic.

## What it does

- Full CRUD for candidates
- Validation with `EmailStr` and typed schemas
- Pagination, sorting, and status filtering
- Partial updates with `PATCH`
- SQLite persistence
- Automatic controller discovery
- AST-based endpoint extraction
- Dynamic OpenAPI 3.0 generation
- Docker support
- CI workflow that runs tests and documentation scripts

## Project Structure

- `main.py` - FastAPI application entrypoint
- `database.py` - Engine, session, and dependency wiring
- `models.py` - SQLAlchemy candidate model
- `schemas.py` - Pydantic request and response schemas
- `crud.py` - Database logic and business rules
- `routers/` - API routes
- `detect_controllers.py` - Finds controller files automatically
- `extract_endpoints.py` - Extracts endpoints from route decorators
- `generate_openapi.py` - Builds `openapi_generated.json`
- `Dockerfile` - Backend container image
- `docker-compose.yml` - Local backend and frontend orchestration
- `.github/workflows/ci.yml` - CI pipeline

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the API:

```bash
uvicorn main:app --reload
```

4. Visit:
- `http://127.0.0.1:8000/docs`

## Candidate Endpoints

- `POST /api/v1/candidates/`
- `GET /api/v1/candidates/`
- `GET /api/v1/candidates/{candidate_id}`
- `PUT /api/v1/candidates/{candidate_id}`
- `PATCH /api/v1/candidates/{candidate_id}`
- `DELETE /api/v1/candidates/{candidate_id}`

### Query Parameters

- `name` - Filter by candidate name
- `status` - Filter by candidate status
- `skip` - Offset for pagination
- `limit` - Page size
- `sort_by` - `created_at`, `name`, `experience`, or `status`
- `sort_order` - `asc` or `desc`

The list endpoint returns the total count in the `X-Total-Count` response header.

## Documentation Pipeline

Run the documentation workflow manually if needed:

```bash
python detect_controllers.py
python extract_endpoints.py
python generate_openapi.py
```

This produces:
- `detected_controllers.json`
- `detected_endpoints.json`
- `openapi_generated.json`

## Docker

Run the full stack with Docker Compose:

```bash
docker compose up --build
```

Backend:
- `http://127.0.0.1:8000/docs`

Frontend:
- `http://127.0.0.1:3000`

## Bonus Notes

- Endpoint descriptions are generated with a rule-based AI-style summarizer so they can be upgraded later to a real LLM.
- The scripts log controller and endpoint changes to `documentation_keeper.log`.
- A good dashboard UI next step would be a small React or Next.js admin panel with candidate cards, filters by status, and an OpenAPI viewer side panel.
