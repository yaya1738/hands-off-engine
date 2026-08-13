import pytest

from ai.factory.local_agent_executor import FactoryLocalAgentExecutor


def test_rejects_absolute_allowed_path():
    with pytest.raises(ValueError, match="escapes workspace"):
        FactoryLocalAgentExecutor().execute(
            {"objective": "test"},
            workspace="/tmp/factory",
            allowed_paths=["/etc/passwd"],
        )


def test_rejects_parent_traversal():
    with pytest.raises(ValueError, match="escapes workspace"):
        FactoryLocalAgentExecutor().execute(
            {"objective": "test"},
            workspace="/tmp/factory",
            allowed_paths=["../outside.py"],
        )


def test_normalizes_authorized_relative_paths():
    result = FactoryLocalAgentExecutor().execute(
        {"objective": "test"},
        workspace="/tmp/factory",
        allowed_paths=["src/./module.py"],
    )
    assert result["allowed_paths"] == ["src/module.py"]
