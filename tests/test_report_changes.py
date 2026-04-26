"""Tests for repository change reporting."""

from __future__ import annotations

from report_changes import build_change_report, classify_change


def test_classify_change_labels_api_files() -> None:
    assert classify_change("routers/candidates.py") == "api"
    assert classify_change("main.py") == "api"
    assert classify_change("generate_openapi.py") == "api"


def test_classify_change_labels_non_api_files() -> None:
    assert classify_change("README.md") == "non-api"
    assert classify_change("tests/test_main.py") == "non-api"


def test_build_change_report_groups_changes() -> None:
    changes = [
        {
            "status": "M",
            "path": "routers/candidates.py",
            "classification": "api",
            "added_lines": 3,
            "deleted_lines": 1,
        },
        {
            "status": "M",
            "path": "README.md",
            "classification": "non-api",
            "added_lines": 5,
            "deleted_lines": 2,
        },
    ]

    report = build_change_report(changes, "base-sha", "head-sha")

    assert report["range"] == {"base": "base-sha", "head": "head-sha"}
    assert report["summary"] == {
        "total_files": 2,
        "api_files": 1,
        "non_api_files": 1,
        "added_lines": 8,
        "deleted_lines": 3,
    }
    assert report["api_changes"][0]["path"] == "routers/candidates.py"
    assert report["non_api_changes"][0]["path"] == "README.md"
