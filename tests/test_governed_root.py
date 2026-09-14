import json
from pathlib import Path

import autonomous.governed_root as root


def test_record_decisions_persists_fail_closed_state(tmp_path):
    root.QUEUE = tmp_path / "command_queue.jsonl"
    root.DECISIONS = tmp_path / "governed_decisions.json"
    root.QUEUE.write_text(
        json.dumps({"id": "live-1", "action": "execute", "mode": "LIVE", "status": "pending"}) + "\n"
    )

    decisions = root.record_decisions()

    assert decisions["live-1"]["decision"] == "approval_required"
    assert decisions["live-1"]["execution_enabled"] is False
    persisted = json.loads(root.DECISIONS.read_text())
    assert persisted == decisions


def test_record_decisions_tracks_explicit_approval_without_enabling_execution(tmp_path):
    root.QUEUE = tmp_path / "command_queue.jsonl"
    root.DECISIONS = tmp_path / "governed_decisions.json"
    root.QUEUE.write_text(
        json.dumps({
            "id": "live-2",
            "action": "execute",
            "mode": "LIVE",
            "approval_status": "approved",
            "status": "pending",
        }) + "\n"
    )

    decisions = root.record_decisions()

    assert decisions["live-2"]["decision"] == "approved"
    assert decisions["live-2"]["execution_enabled"] is False
    assert decisions["live-2"]["approval_required"] is True


def test_record_decisions_ignores_malformed_queue_lines(tmp_path):
    root.QUEUE = tmp_path / "command_queue.jsonl"
    root.DECISIONS = tmp_path / "governed_decisions.json"
    root.QUEUE.write_text("not-json\n" + json.dumps({"id": "dry-1", "status": "pending"}) + "\n")

    decisions = root.record_decisions()

    assert decisions["dry-1"]["decision"] == "dryrun_only"
    assert decisions["dry-1"]["execution_enabled"] is False
