from scripts.authority_continuation import continue_from_authority


def test_unapproved_or_missing_authority_fails_closed(tmp_path):
    assert continue_from_authority({}, repo_root=tmp_path)["status"] == "skipped"
    assert continue_from_authority({"authority_decision": {"available": True, "decision": "denied"}}, repo_root=tmp_path)["reason"] == "not_approved"


def test_approved_authority_continues_with_explicit_correlation(tmp_path):
    result = continue_from_authority(
        {"authority_decision": {
            "available": True,
            "msg_id": "m-1",
            "reply_to": "r-1",
            "task_id": "t-1",
            "decision": "approved",
            "execution_enabled": True,
        }},
        repo_root=tmp_path,
    )
    assert result == {"status": "published", "msg_id": "m-1", "task_id": "t-1"}
    text = (tmp_path / "ai" / "coordination" / "messages.jsonl").read_text()
    assert '"event_type": "authority_continuation"' in text
    assert '"reply_to": "r-1"' in text
    assert '"task_id": "t-1"' in text
    assert '"execution_enabled": false' in text
