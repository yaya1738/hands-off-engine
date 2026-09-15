"""Focused tests for the lifecycle dashboard view."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.lifecycle_dashboard as ld


def _make_lifecycle(tmp_path):
    """Write a small lifecycle fixture to tmp and return path."""
    f = tmp_path / "task_lifecycle.json"
    data = {
        "task-a": {
            "task_id": "task-a", "sender": "factory", "recipient": "anyclaw",
            "action": "health_check", "correlation_id": "c1",
            "states": {"sent": "09-14T10:00:00", "completed": "09-14T10:00:10",
                       "result_published": "09-14T10:00:12"},
            "updated_at": "09-14T10:00:12",
        },
        "task-b": {
            "task_id": "task-b", "sender": "factory", "recipient": "anyclaw",
            "action": "system_status",
            "states": {"sent": "09-14T10:01:00"},
            "updated_at": "09-14T10:01:00",
        },
        "task-c": {
            "task_id": "task-c", "sender": "anyclaw", "recipient": "factory",
            "action": "read_file_fact", "correlation_id": "c2",
            "states": {"sent": "09-14T10:02:00", "executing": "09-14T10:02:01"},
            "updated_at": "09-14T10:02:01",
        },
    }
    f.write_text(json.dumps(data))
    return f


def test_load_and_build_rows(tmp_path):
    f = _make_lifecycle(tmp_path)
    lifecycle = ld.load_lifecycle(f)
    rows = ld.build_rows(lifecycle)
    assert len(rows) == 3
    states = {r["task_id"]: r["current"] for r in rows}
    assert states["task-a"] == "result_published"
    assert states["task-b"] == "sent"
    assert states["task-c"] == "executing"
    # Sorted by updated_at descending
    assert rows[0]["task_id"] == "task-c"


def test_json_export_smoke(tmp_path):
    f = _make_lifecycle(tmp_path)
    lifecycle = ld.load_lifecycle(f)
    rows = ld.build_rows(lifecycle)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ld.render_json(rows)
    out = json.loads(buf.getvalue())
    assert out["summary"]["task_count"] == 3
    assert out["summary"]["by_state"]["sent"] == 1
    assert out["summary"]["by_state"]["result_published"] == 1
    assert "task-c" in [t["task_id"] for t in out["tasks"]]


def test_summary_counters(tmp_path):
    f = _make_lifecycle(tmp_path)
    lifecycle = ld.load_lifecycle(f)
    rows = ld.build_rows(lifecycle)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ld.render_summary(rows)
    out = buf.getvalue()
    assert "State distribution" in out
    assert "Party activity" in out
    assert "factory" in out
    assert "anyclaw" in out


def test_empty_lifecycle(tmp_path):
    f = tmp_path / "task_lifecycle.json"
    f.write_text("{}")
    lifecycle = ld.load_lifecycle(f)
    rows = ld.build_rows(lifecycle)
    assert rows == []
