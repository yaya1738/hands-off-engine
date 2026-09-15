"""Focused tests for lifecycle/health trend analysis."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.lifecycle_trends as lt


def _write_lifecycle(tmp_path):
    f = tmp_path / "task_lifecycle.json"
    data = {
        "task-a": {
            "task_id": "task-a", "sender": "factory", "recipient": "anyclaw",
            "action": "health_check",
            "states": {"sent": "2026-09-14T10:00:00", "result_published": "2026-09-14T10:00:10"},
            "updated_at": "2026-09-14T10:00:10",
        },
        "task-b": {
            "task_id": "task-b", "sender": "factory", "recipient": "anyclaw",
            "action": "system_status",
            "states": {"sent": "2026-09-14T11:00:00"},
            "updated_at": "2026-09-14T11:00:00",
        },
        "task-c": {
            "task_id": "task-c", "sender": "anyclaw", "recipient": "factory",
            "action": "read_file_fact",
            "states": {"sent": "2026-09-15T01:00:00", "result_published": "2026-09-15T01:00:05"},
            "updated_at": "2026-09-15T01:00:05",
        },
    }
    f.write_text(json.dumps(data))
    return f


def test_task_trends_per_day(tmp_path):
    f = _write_lifecycle(tmp_path)
    trends = lt.task_trends(lt._load_json(f))
    assert "2026-09-14" in trends
    assert trends["2026-09-14"]["total"] == 2
    assert trends["2026-09-14"]["completed"] == 1
    assert trends["2026-09-14"]["stuck"] == 1
    assert trends["2026-09-15"]["total"] == 1
    assert trends["2026-09-15"]["completed"] == 1


def test_state_distribution(tmp_path):
    f = _write_lifecycle(tmp_path)
    dist = lt.state_distribution(lt._load_json(f))
    assert dist["result_published"] == 2
    assert dist["sent"] == 1
    assert sum(dist.values()) == 3


def test_learning_summary():
    lt.LEARNING_STATE = Path("/nonexistent/learning.json")
    s = lt.learning_summary()
    assert s["total_tasks"] == 0  # fails safe on missing file


def test_health_trends_missing_log(tmp_path):
    lt.HEALTH_LOG = tmp_path / "missing_health.jsonl"
    assert lt.health_trends() == {}


def test_parse_period():
    assert lt._parse_period("2026-09-14T10:00:00+00:00") == "2026-09-14"
    assert lt._parse_period("2026-09-14T10:00:00Z") == "2026-09-14"
    assert lt._parse_period("garbage") == "unknown"
    assert lt._parse_period("") == "unknown"
