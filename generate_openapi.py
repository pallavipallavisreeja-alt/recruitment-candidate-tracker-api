"""Generate an OpenAPI 3.0 document from detected FastAPI endpoints."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ENDPOINTS_FILE = ROOT / "detected_endpoints.json"
OUTPUT_FILE = ROOT / "openapi_generated.json"
LOG_FILE = ROOT / "documentation_keeper.log"

logger = logging.getLogger("documentation_keeper.generate_openapi")
PATH_PARAM_PATTERN = re.compile(r"\{([^}]+)\}")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )


def _load_endpoints() -> list[dict[str, Any]]:
    if not ENDPOINTS_FILE.exists():
        raise FileNotFoundError(
            f"{ENDPOINTS_FILE.name} does not exist. Run extract_endpoints.py first."
        )
    return json.loads(ENDPOINTS_FILE.read_text(encoding="utf-8"))


def _camelize(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_\-/ ]+", value) if part)



def _resource_name(path: str) -> str:
    segments = [segment for segment in path.split("/") if segment and not segment.startswith("{")]
    if not segments:
        return "Root"
    name = segments[-1]
    if name.endswith("ies") and len(name) > 3:
        name = name[:-3] + "y"
    elif name.endswith("s") and len(name) > 1:
        name = name[:-1]
    return _camelize(name)



def _generate_description(method: str, path: str, handler: str) -> str:
    resource = _resource_name(path)
    if method == "GET" and "{" in path:
        return f"Fetch a single {resource.lower()} record by identifier."
    if method == "GET":
        return f"List {resource.lower()} records and optionally filter them using query parameters."
    if method == "POST":
        return f"Create a new {resource.lower()} record and persist it to the database."
    if method == "PUT":
        return f"Update an existing {resource.lower()} record using the payload supplied by the caller."
    if method == "PATCH":
        return f"Partially update an existing {resource.lower()} record."
    if method == "DELETE":
        return f"Delete the targeted {resource.lower()} record from the database."
    return f"Endpoint generated from handler {handler}."



def _generate_summary(method: str, path: str, handler: str) -> str:
    resource = _resource_name(path)
    if method == "GET" and "{" in path:
        return f"Get {resource}"
    if method == "GET":
        return f"List {resource}s"
    return f"{method.title()} {resource}"



def _path_parameters(path: str) -> list[dict[str, Any]]:
    parameters = []
    for param in PATH_PARAM_PATTERN.findall(path):
        parameters.append(
            {
                "name": param,
                "in": "path",
                "required": True,
                "schema": {"type": "integer" if param.endswith("id") else "string"},
                "description": f"Path parameter `{param}`.",
            }
        )
    return parameters



def _candidate_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "example": 1},
            "name": {"type": "string", "example": "Ava Patel"},
            "email": {"type": "string", "format": "email", "example": "ava@example.com"},
            "skills": {"type": "array", "items": {"type": "string"}, "example": ["Python", "FastAPI"]},
            "experience": {"type": "integer", "minimum": 0, "example": 5},
            "status": {"type": "string", "example": "screening"},
            "created_at": {"type": "string", "format": "date-time"},
        },
        "required": ["id", "name", "email", "skills", "experience", "status", "created_at"],
    }



def _candidate_create_schema() -> dict[str, Any]:
    schema = _candidate_schema().copy()
    schema["required"] = ["name", "email"]
    schema["properties"] = {k: v for k, v in schema["properties"].items() if k != "id" and k != "created_at"}
    return schema



def _candidate_update_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 2},
            "email": {"type": "string", "format": "email"},
            "skills": {"type": "array", "items": {"type": "string"}},
            "experience": {"type": "integer", "minimum": 0},
            "status": {"type": "string"},
        },
    }



def _request_body_for_endpoint(path: str, method: str) -> dict[str, Any] | None:
    if "/candidates" not in path:
        return None
    if method == "POST":
        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/CandidateCreate"}
                }
            },
        }
    if method in {"PUT", "PATCH"}:
        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/CandidateUpdate"}
                }
            },
        }
    return None



def _response_for_endpoint(method: str, path: str) -> dict[str, Any]:
    if method == "DELETE":
        return {"204": {"description": "Candidate deleted successfully."}}
    if method == "POST":
        return {
            "201": {
                "description": "Candidate created successfully.",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Candidate"}}},
            }
        }
    if method in {"PUT", "PATCH"}:
        return {
            "200": {
                "description": "Candidate updated successfully.",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Candidate"}}},
            }
        }
    if method == "GET" and "{" in path:
        return {
            "200": {
                "description": "Candidate retrieved successfully.",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Candidate"}}},
            }
        }
    if method == "GET":
        return {
            "200": {
                "description": "Candidate list retrieved successfully.",
                "headers": {
                    "X-Total-Count": {
                        "description": "Total number of matching candidates before pagination.",
                        "schema": {"type": "integer"},
                    }
                },
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Candidate"},
                        }
                    }
                },
            }
        }
    return {
        "200": {
            "description": "Operation completed successfully.",
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Candidate"}}},
        }
    }



def _operation_for_endpoint(endpoint: dict[str, Any]) -> dict[str, Any]:
    method = endpoint.get("method", "GET").lower()
    path = endpoint.get("path", "/")
    handler = endpoint.get("handler", "handler")
    operation = {
        "summary": _generate_summary(endpoint.get("method", "GET"), path, handler),
        "description": _generate_description(endpoint.get("method", "GET"), path, handler),
        "operationId": f"{method}_{handler}",
        "tags": ["Candidates" if "/candidates" in path else "System"],
        "responses": _response_for_endpoint(endpoint.get("method", "GET"), path),
        "parameters": _path_parameters(path),
    }

    if path == "/api/v1/candidates" and endpoint.get("method", "GET") == "GET":
        operation["parameters"].extend(
            [
                {
                    "name": "name",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "description": "Case-insensitive candidate name filter.",
                },
                {
                    "name": "status",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "description": "Filter candidates by status.",
                },
                {
                    "name": "skip",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer", "minimum": 0, "default": 0},
                    "description": "Number of records to skip.",
                },
                {
                    "name": "limit",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
                    "description": "Maximum records to return.",
                },
                {
                    "name": "sort_by",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string", "enum": ["created_at", "name", "experience", "status"]},
                    "description": "Sort field.",
                },
                {
                    "name": "sort_order",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string", "enum": ["asc", "desc"]},
                    "description": "Sort direction.",
                },
            ]
        )

    if method in {"post", "put", "patch"}:
        request_body = _request_body_for_endpoint(path, endpoint.get("method", "GET"))
        if request_body:
            operation["requestBody"] = request_body

    if not operation["parameters"]:
        operation.pop("parameters")

    return operation



def generate_openapi(endpoints_file: str | Path = ENDPOINTS_FILE, output_file: str | Path = OUTPUT_FILE) -> dict[str, Any]:
    _configure_logging()
    endpoints_path = Path(endpoints_file)
    endpoints = _load_endpoints() if endpoints_path == ENDPOINTS_FILE else json.loads(endpoints_path.read_text(encoding="utf-8"))

    openapi: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": "Recruitment Candidate Tracker API",
            "version": "1.0.0",
            "description": "Dynamically generated OpenAPI specification for the candidate tracker service.",
        },
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {},
        "components": {
            "schemas": {
                "Candidate": _candidate_schema(),
                "CandidateCreate": _candidate_create_schema(),
                "CandidateUpdate": _candidate_update_schema(),
            }
        },
    }

    for endpoint in endpoints:
        path = endpoint["path"]
        method = endpoint["method"].lower()
        openapi["paths"].setdefault(path, {})[method] = _operation_for_endpoint(endpoint)

    output_path = Path(output_file)
    output_path.write_text(json.dumps(openapi, indent=2), encoding="utf-8")
    logger.info("OpenAPI specification saved to %s", output_path.name)
    return openapi


if __name__ == "__main__":
    generate_openapi()
