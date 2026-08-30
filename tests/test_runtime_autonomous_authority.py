from unittest.mock import Mock

from ai.factory.runtime import FactoryRuntime


def test_autonomous_execute_delegates_to_authority_gateway(monkeypatch):
    """Legacy runtime ingress must not own the autonomous execution transition."""
    authority = Mock()
    authority.execute_autonomous.return_value = {
        "status": "delegated",
    }

    monkeypatch.setattr(
        "ai.factory.authority_gateway.FactoryAuthorityGateway",
        lambda runtime=None: authority,
    )

    runtime = FactoryRuntime()
    runtime.execute = Mock(side_effect=AssertionError("runtime.execute bypassed authority gateway"))

    result = runtime.autonomous_execute("test objective")

    assert result == {"status": "delegated"}
    authority.execute_autonomous.assert_called_once_with("test objective")
    runtime.execute.assert_not_called()
