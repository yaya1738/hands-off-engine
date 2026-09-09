import json

from tools.factory_forensics.execution_integrity import audit


def test_audit_accepts_valid_terminal_lifecycle(tmp_path):
    path = tmp_path / "journal.json"
    path.write_text(json.dumps([
        {"execution_id": "e1", "state": "STARTED", "intent": {}, "ts": "2026-01-01T00:00:00+00:00"},
        {"execution_id": "e1", "state": "COMPLETED", "intent": {}, "ts": "2026-01-01T00:00:01+00:00"},
    ]), encoding="utf-8")
    result = audit(path)
    assert result["valid"] is True
    assert result["interrupted"] == 0


def test_audit_rejects_duplicate_terminal_transition(tmp_path):
    path = tmp_path / "journal.json"
    path.write_text(json.dumps([
        {"execution_id": "e1", "state": "STARTED", "intent": {}, "ts": "2026-01-01T00:00:00+00:00"},
        {"execution_id": "e1", "state": "COMPLETED", "intent": {}, "ts": "2026-01-01T00:00:01+00:00"},
        {"execution_id": "e1", "state": "FAILED", "intent": {}, "ts": "2026-01-01T00:00:02+00:00"},
    ]), encoding="utf-8")
    result = audit(path)
    assert result["valid"] is False
    assert any("invalid transition" in error for error in result["errors"])


def test_audit_treats_missing_journal_as_empty_not_corrupt(tmp_path):
    result = audit(tmp_path / "missing.json")
    assert result["valid"] is True
    assert result["missing"] is True
