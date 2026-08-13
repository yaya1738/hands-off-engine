import json

import pytest

from ai.factory.agent_result_validator import AgentResultValidator


ALLOWED = ["tests/example.py"]
VALID = {"path": "tests/example.py", "operation": "replace_text", "old": "old", "new": "new"}


def test_valid_edit_is_normalized():
    assert AgentResultValidator.validate(json.dumps(VALID), ALLOWED) == VALID


@pytest.mark.parametrize("raw", ["not json", [], None, {"path": "tests/example.py"}])
def test_invalid_result_rejected(raw):
    with pytest.raises((ValueError, TypeError)):
        AgentResultValidator.validate(raw, ALLOWED)


def test_unauthorized_path_rejected():
    edit = {**VALID, "path": "src/secret.py"}
    with pytest.raises(PermissionError):
        AgentResultValidator.validate(edit, ALLOWED)


def test_unsupported_operation_rejected():
    edit = {**VALID, "operation": "write_file"}
    with pytest.raises(ValueError):
        AgentResultValidator.validate(edit, ALLOWED)


def test_wrong_types_and_empty_old_rejected():
    with pytest.raises(TypeError):
        AgentResultValidator.validate({**VALID, "old": 1}, ALLOWED)
    with pytest.raises(ValueError):
        AgentResultValidator.validate({**VALID, "old": ""}, ALLOWED)
