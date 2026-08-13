from ai.factory.autonomy_manager import FactoryAutonomyManager


class FakeRuntime:
    def __init__(self):
        self.legacy_called = False

    def component_inventory(self):
        return {"component_count": 1}

    def autonomous_execute(self, objective):
        self.legacy_called = True
        raise AssertionError("legacy runtime.autonomous_execute bypass was used")


class FakeAuthority:
    def __init__(self):
        self.objectives = []

    def execute_autonomous(self, objective):
        self.objectives.append(objective)
        return {"status": "executed", "objective": objective}


def test_execute_routes_through_authority_gateway_without_legacy_bypass():
    runtime = FakeRuntime()
    authority = FakeAuthority()
    manager = FactoryAutonomyManager(runtime)
    manager._authority_gateway = authority

    result = manager.execute("migrate execution authority")

    assert result["execution"] == {
        "status": "executed",
        "objective": "migrate execution authority",
    }
    assert authority.objectives == ["migrate execution authority"]
    assert runtime.legacy_called is False
