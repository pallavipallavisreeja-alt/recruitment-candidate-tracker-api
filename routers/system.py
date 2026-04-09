"""System routes for generated documentation and API history."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api_history import list_versions

router = APIRouter(prefix="/api/v1/system", tags=["System"])
OPENAPI_PATH = Path("openapi_generated.json")


@router.get("/generated-docs", summary="Get generated OpenAPI document")
def get_generated_docs():
    if not OPENAPI_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated OpenAPI document is not available yet.",
        )
    return JSONResponse(content=json.loads(OPENAPI_PATH.read_text(encoding="utf-8")))


@router.get("/versions", summary="List API artifact versions")
def get_versions():
    return list_versions()
