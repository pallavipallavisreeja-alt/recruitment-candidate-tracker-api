"""System routes for generated documentation and API history."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api_history import list_versions

router = APIRouter(prefix="/api/v1/system", tags=["System"])
OPENAPI_PATH = Path("openapi_generated.json")


@router.get("/generated-docs", summary="Get generated OpenAPI document",
            response_model=dict)
def get_generated_docs():
    if not OPENAPI_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated OpenAPI document is not available yet."
        )
    
    import json
    with open(OPENAPI_PATH) as f:
        return json.load(f)

@router.get("/versions", summary="List API artifact versions")
def get_versions():
    return [
        {"version": "v1", "status": "active"},
        {"version": "v2", "status": "beta"}
    ]
