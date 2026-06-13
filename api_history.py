"""Helpers for storing and comparing generated API artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import desc

from database import Base, SessionLocal, engine
from models import ApiVersion


def _serialize_content(content: Any) -> str:
    return json.dumps(content, indent=2, sort_keys=True)


def _deserialize_content(content: str) -> Any:
    return json.loads(content)


def next_version(artifact_type: str) -> int:
    """Return the next version number for an artifact type."""

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        latest = (
            db.query(ApiVersion)
            .filter(ApiVersion.artifact_type == artifact_type)
            .order_by(desc(ApiVersion.version))
            .first()
        )
        return 1 if latest is None else latest.version + 1
    finally:
        db.close()


def record_artifact_version(
    artifact_type: str,
    file_path: str | Path,
    content: Any,
    change_summary: str | None = None,
) -> ApiVersion:
    """Persist a new artifact snapshot to the API version history table."""

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        version = next_version(artifact_type)
        record = ApiVersion(
            artifact_type=artifact_type,
            version=version,
            file_path=str(file_path),
            content_json=_serialize_content(content),
            change_summary=change_summary,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def list_versions(artifact_type: str | None = None) -> list[dict[str, Any]]:
    """Return stored artifact versions ordered newest-first."""

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        query = db.query(ApiVersion)
        if artifact_type:
            query = query.filter(ApiVersion.artifact_type == artifact_type)
        records = query.order_by(desc(ApiVersion.version)).all()
        return [
            {
                "id": record.id,
                "artifact_type": record.artifact_type,
                "version": record.version,
                "file_path": record.file_path,
                "change_summary": record.change_summary,
                "created_at": record.created_at,
                "content": _deserialize_content(record.content_json),
            }
            for record in records
        ]
    finally:
        db.close()


def latest_versions(artifact_type: str, limit: int = 2) -> list[ApiVersion]:
    """Load the most recent versions for an artifact type."""

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        return (
            db.query(ApiVersion)
            .filter(ApiVersion.artifact_type == artifact_type)
            .order_by(desc(ApiVersion.version))
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def is_breaking_change(old: dict, new: dict, added_params, removed_params) -> bool:
    """
    Detects whether an API change is breaking.
    """

    # 1. Parameter removal is always breaking
    if removed_params:
        return True

    # 2. Method change is breaking (GET → POST etc.)
    if old.get("method") != new.get("method"):
        return True

    # 3. Path change is breaking (/users → /user)
    if old.get("path") != new.get("path"):
        return True
    # 4. New required parameters (optional improvement)
    if len(added_params) > 0 and not old.get("optional", True):
        return True
    return False