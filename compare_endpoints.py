"""Compare the two most recent endpoint snapshots."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from api_history import compare_endpoint_snapshots, latest_versions

ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "endpoint_diff.json"
LOG_FILE = ROOT / "documentation_keeper.log"

logger = logging.getLogger("documentation_keeper.compare_endpoints")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )


def _load_latest_snapshots() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = latest_versions("endpoints", limit=2)
    if not records:
        return [], []
    current = json.loads(records[0].content_json)
    previous = json.loads(records[1].content_json) if len(records) > 1 else []
    return previous, current


def compare_endpoints() -> dict[str, list[dict[str, Any]]]:
    """Compare the latest two endpoint versions and persist the diff."""

    _configure_logging()
    previous, current = _load_latest_snapshots()
    diff = compare_endpoint_snapshots(previous, current)
    OUTPUT_FILE.write_text(json.dumps(diff, indent=2), encoding="utf-8")
    logger.info(
        "Endpoint comparison complete: %d added, %d removed",
        len(diff["added"]),
        len(diff["removed"]),
    )
    if diff["added"]:
        logger.info(
            "Added endpoints: %s",
            ", ".join(f"{item['method']} {item['path']}" for item in diff["added"]),
        )
    if diff["removed"]:
        logger.info(
            "Removed endpoints: %s",
            ", ".join(f"{item['method']} {item['path']}" for item in diff["removed"]),
        )
    return diff


if __name__ == "__main__":
    result = compare_endpoints()
    print("Added:", result["added"])
    print("Removed:", result["removed"])
