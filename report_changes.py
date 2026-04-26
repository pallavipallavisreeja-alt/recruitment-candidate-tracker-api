"""Report repository changes and separate API from non-API updates."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "change_report.json"
LOG_FILE = ROOT / "documentation_keeper.log"

API_DIR_PREFIXES = ("routers/",)
API_FILE_NAMES = {
    "api_history.py",
    "compare_endpoints.py",
    "detect_controllers.py",
    "detected_controllers.json",
    "detected_endpoints.json",
    "endpoint_diff.json",
    "extract_endpoints.py",
    "generate_openapi.py",
    "main.py",
    "models.py",
    "openapi_generated.json",
    "schemas.py",
    "crud.py",
}

logger = logging.getLogger("documentation_keeper.report_changes")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _repo_is_dirty() -> bool:
    return bool(_run_git("status", "--porcelain"))


def _resolve_diff_range() -> tuple[str, str | None]:
    before = os.getenv("GITHUB_EVENT_BEFORE")
    current = os.getenv("GITHUB_SHA")
    if before and current and before != "0000000000000000000000000000000000000000":
        return before, current

    if _repo_is_dirty():
        return "HEAD", None

    try:
        previous = _run_git("rev-parse", "HEAD^")
        head = _run_git("rev-parse", "HEAD")
        return previous, head
    except subprocess.CalledProcessError:
        return "HEAD", None


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def classify_change(path: str) -> str:
    """Return `api` for API-related files and `non-api` for everything else."""

    normalized = _normalize_path(path)
    if normalized.startswith(API_DIR_PREFIXES) or normalized in API_FILE_NAMES:
        return "api"
    return "non-api"


def _parse_name_status_line(line: str) -> dict[str, str]:
    parts = line.split("\t")
    status = parts[0]
    if status.startswith(("R", "C")) and len(parts) >= 3:
        return {"status": status, "path": parts[2], "previous_path": parts[1]}
    if len(parts) >= 2:
        return {"status": status, "path": parts[1]}
    return {"status": status, "path": parts[0]}


def _normalize_diff_path(path: str) -> str:
    normalized = _normalize_path(path)
    if " => " in normalized:
        normalized = normalized.split(" => ", 1)[1]
    return normalized


def _load_changed_files(base_ref: str, head_ref: str | None) -> list[dict[str, Any]]:
    if head_ref is None:
        raw_status = _run_git("diff", "--name-status", "--find-renames", base_ref)
        raw_numstat = _run_git("diff", "--numstat", "--find-renames", base_ref)
    else:
        if base_ref == head_ref:
            return []
        raw_status = _run_git("diff", "--name-status", "--find-renames", base_ref, head_ref)
        raw_numstat = _run_git("diff", "--numstat", "--find-renames", base_ref, head_ref)

    numstat_by_path: dict[str, tuple[int, int]] = {}
    for line in raw_numstat.splitlines():
        if not line.strip():
            continue
        added_raw, deleted_raw, path = line.split("\t")
        if added_raw == "-" or deleted_raw == "-":
            added = deleted = 0
        else:
            added = int(added_raw)
            deleted = int(deleted_raw)
        normalized_path = _normalize_diff_path(path)
        numstat_by_path[normalized_path] = (added, deleted)

    changes: list[dict[str, Any]] = []
    for line in raw_status.splitlines():
        if not line.strip():
            continue
        parsed = _parse_name_status_line(line)
        path = _normalize_diff_path(parsed["path"])
        added, deleted = numstat_by_path.get(path, (0, 0))
        classification = classify_change(path)
        changes.append(
            {
                "status": parsed["status"],
                "path": path,
                "classification": classification,
                "added_lines": added,
                "deleted_lines": deleted,
                **({"previous_path": _normalize_path(parsed["previous_path"])} if "previous_path" in parsed else {}),
            }
        )

    return sorted(changes, key=lambda item: (item["classification"], item["path"]))


def build_change_report(changes: list[dict[str, Any]], base_ref: str, head_ref: str | None) -> dict[str, Any]:
    api_changes = [item for item in changes if item["classification"] == "api"]
    non_api_changes = [item for item in changes if item["classification"] == "non-api"]
    total_added = sum(int(item["added_lines"]) for item in changes)
    total_deleted = sum(int(item["deleted_lines"]) for item in changes)

    return {
        "range": {"base": base_ref, "head": head_ref or "WORKTREE"},
        "summary": {
            "total_files": len(changes),
            "api_files": len(api_changes),
            "non_api_files": len(non_api_changes),
            "added_lines": total_added,
            "deleted_lines": total_deleted,
        },
        "changes": changes,
        "api_changes": api_changes,
        "non_api_changes": non_api_changes,
    }


def _format_change(item: dict[str, Any]) -> str:
    status = item["status"]
    path = item["path"]
    added = item["added_lines"]
    deleted = item["deleted_lines"]
    prefix = "API" if item["classification"] == "api" else "non-API"
    if "previous_path" in item:
        return f"{prefix}: {status} {item['previous_path']} -> {path} (+{added} -{deleted})"
    return f"{prefix}: {status} {path} (+{added} -{deleted})"


def report_changes() -> dict[str, Any]:
    """Detect changed files, write a JSON report, and log a readable summary."""

    _configure_logging()
    base_ref, head_ref = _resolve_diff_range()
    changes = _load_changed_files(base_ref, head_ref)
    report = build_change_report(changes, base_ref, head_ref)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

    logger.info(
        "Repository change report complete: %d total file(s), %d API, %d non-API",
        report["summary"]["total_files"],
        report["summary"]["api_files"],
        report["summary"]["non_api_files"],
    )

    if report["api_changes"]:
        logger.info("API changes:")
        for item in report["api_changes"]:
            logger.info("  %s", _format_change(item))
    else:
        logger.info("API changes: none")

    if report["non_api_changes"]:
        logger.info("Non-API changes:")
        for item in report["non_api_changes"]:
            logger.info("  %s", _format_change(item))
    else:
        logger.info("Non-API changes: none")

    logger.info("Saved change report to %s", OUTPUT_FILE.name)
    return report


if __name__ == "__main__":
    result = report_changes()
    print(json.dumps(result, indent=2))
