"""Extract FastAPI endpoints from controller files using AST parsing."""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path
from typing import Any

from api_history import compare_endpoint_snapshots, record_artifact_version
from detect_controllers import find_controller_files

ROOT = Path(__file__).resolve().parent
CONTROLLERS_FILE = ROOT / "detected_controllers.json"
OUTPUT_FILE = ROOT / "detected_endpoints.json"
LOG_FILE = ROOT / "documentation_keeper.log"
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

logger = logging.getLogger("documentation_keeper.extract_endpoints")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
    )


def _load_controller_files() -> list[Path]:
    if CONTROLLERS_FILE.exists():
        try:
            data = json.loads(CONTROLLERS_FILE.read_text(encoding="utf-8"))
            return [ROOT / Path(item) for item in data]
        except json.JSONDecodeError:
            logger.warning("Controller index was invalid JSON; rescanning repository")
    return [ROOT / Path(item) for item in find_controller_files()]


def _get_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    path = path.replace("//", "/")
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path


def _combine_paths(prefix: str, route: str) -> str:
    prefix = prefix.rstrip("/")
    route = route if route.startswith("/") else f"/{route}"
    return _normalize_path(f"{prefix}{route}")


def _extract_router_prefixes(tree: ast.AST) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target_name = node.targets[0].id
        if not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if not isinstance(func, ast.Name) or func.id != "APIRouter":
            continue
        for kw in node.value.keywords:
            if kw.arg == "prefix":
                prefix = _get_string(kw.value)
                if prefix:
                    prefixes[target_name] = prefix
    return prefixes


def _extract_decorator_route(decorator: ast.AST) -> tuple[str | None, str | None]:
    if not isinstance(decorator, ast.Call):
        return None, None
    if not isinstance(decorator.func, ast.Attribute):
        return None, None

    method_name = decorator.func.attr.lower()
    if method_name not in HTTP_METHODS:
        return None, None

    route_path = None
    if decorator.args:
        route_path = _get_string(decorator.args[0])
    if route_path is None:
        for kw in decorator.keywords:
            if kw.arg == "path":
                route_path = _get_string(kw.value)
                break

    return method_name.upper(), route_path


def _collect_endpoints(file_path: Path) -> list[dict[str, Any]]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    router_prefixes = _extract_router_prefixes(tree)
    endpoints: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            method, route_path = _extract_decorator_route(decorator)
            if not method or route_path is None:
                continue

            router_name = None
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and isinstance(decorator.func.value, ast.Name):
                router_name = decorator.func.value.id

            prefix = router_prefixes.get(router_name or "", "")
            full_path = _combine_paths(prefix, route_path)
            endpoints.append(
                {
                    "method": method,
                    "path": full_path,
                    "raw_path": route_path,
                    "router_prefix": prefix,
                    "file": str(file_path.relative_to(ROOT)),
                    "handler": node.name,
                    "line": node.lineno,
                }
            )

    return endpoints


def _log_changes(current: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    previous: list[dict[str, Any]] = []
    if OUTPUT_FILE.exists():
        try:
            previous = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = []

    diff = compare_endpoint_snapshots(previous, current)
    added = diff["added"]
    removed = diff["removed"]

    if added:
        logger.info(
            "Detected endpoint additions: %s",
            ", ".join(f"{item['method']} {item['path']} ({item.get('handler', item.get('file', ''))})" for item in added),
        )
    if removed:
        logger.info(
            "Detected endpoint removals: %s",
            ", ".join(f"{item['method']} {item['path']} ({item.get('handler', item.get('file', ''))})" for item in removed),
        )
    if not added and not removed:
        logger.info("No endpoint changes detected")
    return diff


def main() -> list[dict[str, Any]]:
    _configure_logging()
    all_endpoints: list[dict[str, Any]] = []

    for controller in _load_controller_files():
        if not controller.exists():
            logger.warning("Controller file missing: %s", controller)
            continue
        all_endpoints.extend(_collect_endpoints(controller))

    all_endpoints.sort(key=lambda item: (item["path"], item["method"], item["handler"]))
    diff = _log_changes(all_endpoints)
    OUTPUT_FILE.write_text(json.dumps(all_endpoints, indent=2), encoding="utf-8")
    record_artifact_version(
        "endpoints",
        OUTPUT_FILE,
        all_endpoints,
        change_summary=f"added={len(diff['added'])}, removed={len(diff['removed'])}",
    )
    logger.info("Saved %d endpoint(s) to %s", len(all_endpoints), OUTPUT_FILE.name)
    return all_endpoints


if __name__ == "__main__":
    for endpoint in main():
        print(f"{endpoint['method']} {endpoint['path']} -> {endpoint['handler']}")
