from scripts.authority_request_publisher import publish_authority_request


def test_invalid_request_fails_closed():
    assert publish_authority_request(None) == {"status": "skipped", "reason": "invalid_request"}


def test_missing_correlation_fails_closed():
    assert publish_authority_request({"command": {"objective": "improve"}}) == {
        "status": "skipped",
        "reason": "missing_correlation",
    }


def test_authority_request_is_explicitly_pending_and_non_executing(tmp_path):
    root = tmp_path
    messages = root / "ai" / "coordination" / "messages.jsonl"
    messages.parent.mkdir(parents=True)
    result = publish_authority_request(
        {
            "command": {
                "objective": "improve interaction reliability",
                "mode": "DRYRUN",
                "correlation": {"msg_id": "m-1", "task_id": "t-1"},
                "priority": 0.8,
            }
        },
        repo_root=root,
    )
    assert result["status"] == "published"
    text = messages.read_text()
    assert "authority_request" in text
    assert '"msg_id": "m-1"' in text
    assert '"task_id": "t-1"' in text
    assert '"approval_status": "pending"' in text
    assert '"mode": "DRYRUN"' in text


def test_publication_is_idempotent(tmp_path):
    root = tmp_path
    messages = root / "ai" / "coordination" / "messages.jsonl"
    messages.parent.mkdir(parents=True)
    request = {
        "command": {
            "objective": "improve",
            "correlation": {"msg_id": "m-2", "task_id": "t-2"},
        }
    }
    first = publish_authority_request(request, repo_root=root)
    second = publish_authority_request(request, repo_root=root)
    assert first["status"] == "published"
    assert second["status"] == "already_published"
    assert len(messages.read_text().splitlines()) == 1
