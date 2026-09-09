import json

import pytest

from ai.factory.agent_result_validator import AgentResultValidator
from tools.factory_forensics.validator import extract_authorized_edit


ALLOWED = ["tests/example.py"]
VALID = {"path": "tests/example.py", "operation": "replace_text", "old": "old", "new": "new"}


def test_json_extra_keys_cannot_smuggle_commands():
    payload = {**VALID, "command": "rm -rf /", "shell": True}
    with pytest.raises(ValueError):
        AgentResultValidator.validate(json.dumps(payload), ALLOWED)


def test_path_traversal_is_rejected():
    payload = {**VALID, "path": "tests/../secrets.txt"}
    with pytest.raises(PermissionError):
        AgentResultValidator.validate(payload, ALLOWED)


def test_wrong_operation_and_types_are_rejected():
    payload = {**VALID, "operation": "execute", "new": {"command": "echo pwned"}}
    with pytest.raises((ValueError, TypeError)):
        AgentResultValidator.validate(payload, ALLOWED)


def test_canary_extractor_rejects_unapproved_content_even_when_path_matches():
    raw = json.dumps({"path": "tests/example.py", "content": "UNAUTHORIZED"})
    assert extract_authorized_edit(raw, "tests/example.py", {"AUTHORIZED"}) is None


def test_canary_extractor_ignores_decoy_json_before_authorized_edit():
    raw = "model chatter {\"path\": \"tests/example.py\", \"content\": \"BAD\"} " + json.dumps(
        {"path": "tests/example.py", "content": "AUTHORIZED"}
    )
    assert extract_authorized_edit(raw, "tests/example.py", {"AUTHORIZED"}) == {
        "path": "tests/example.py",
        "content": "AUTHORIZED",
    }


def test_canary_extractor_strips_terminal_escape_sequences():
    raw = "\x1b[31m" + json.dumps({"path": "tests/example.py", "content": "AUTHORIZED"}) + "\x1b[0m"
    assert extract_authorized_edit(raw, "tests/example.py", {"AUTHORIZED"}) is not None
