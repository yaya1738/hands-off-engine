import ai.autonomous_change as autonomous_change


class FakeQueue:
    def __init__(self):
        self.change = None

    def add_change(self, **kwargs):
        self.change = {"id": "test-change", **kwargs}
        return "test-change"

    def approve(self, change_id):
        return change_id == "test-change"

    def execute_approved(self, change_id):
        return {
            "success": False,
            "error": "Execution blocked: governed execution required",
        }


def test_safe_change_is_not_reported_as_applied_when_execution_is_blocked(monkeypatch):
    monkeypatch.setattr(autonomous_change, "ApprovalQueue", FakeQueue)
    monkeypatch.setattr(autonomous_change, "needs_approval", lambda change_type, files: False)

    result = autonomous_change.propose_change(
        title="safe-looking change",
        description="must still pass through governed execution",
        change_type="documentation",
        files=["docs/example.md"],
        action={"type": "write_file", "file_path": "/tmp/example", "content": "x"},
        risk_level="low",
    )

    assert result["applied"] is False
    assert result["status"] == "execution_blocked"
    assert result["result"]["success"] is False
