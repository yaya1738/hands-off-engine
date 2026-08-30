from ai.factory.runtime import FactoryRuntime


def test_runtime_has_no_legacy_autonomous_execute_bypass():
    """Autonomous execution must not be exposed as a second runtime ingress."""
    assert not hasattr(FactoryRuntime, "autonomous_execute")
