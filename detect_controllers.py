"""Detect API controller files in the repository."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IGNORE_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}
LOG_FILE = ROOT / "documentation_keeper.log"
OUTPUT_FILE = ROOT / "detected_controllers.json"
ROUTE_PATTERN = re.compile(r"@\s*\w+\.(get|post|put|delete|patch|options|head)\b", re.IGNORECASE)

logger = logging.getLogger("documentation_keeper.detect_controllers")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )


def _should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def find_controller_files(base_dir: Path = ROOT) -> list[str]:
    """Return Python files that look like FastAPI controller modules."""

    controller_files: list[str] = []
    for file_path in base_dir.rglob("*.py"):
        if _should_skip(file_path):
            continue
        if file_path.name.startswith("__"):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

        if "APIRouter" in content and ROUTE_PATTERN.search(content):
            controller_files.append(str(file_path.relative_to(base_dir)))

    return sorted(controller_files)


def _log_changes(current: list[str]) -> None:
    previous: list[str] = []
    if OUTPUT_FILE.exists():
        try:
            previous = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = []

    added = sorted(set(current) - set(previous))
    removed = sorted(set(previous) - set(current))

    if added:
        logger.info("Detected controller additions: %s", ", ".join(added))
    if removed:
        logger.info("Detected controller removals: %s", ", ".join(removed))
    if not added and not removed:
        logger.info("No controller file changes detected")


def main() -> list[str]:
    _configure_logging()
    controllers = find_controller_files()
    _log_changes(controllers)
    OUTPUT_FILE.write_text(json.dumps(controllers, indent=2), encoding="utf-8")
    logger.info("Saved %d controller file(s) to %s", len(controllers), OUTPUT_FILE.name)
    return controllers


if __name__ == "__main__":
    for controller in main():
        print(controller)
