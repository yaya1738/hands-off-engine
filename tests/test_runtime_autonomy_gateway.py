from factory_runtime_autonomy_gateway import FactoryRuntimeAutonomyGateway


class _Requirements:
    def __init__(self):
        self.calls = 0

    def evaluate(self, objective):
        self.calls += 1
        return {"decision": {"action": "route_to_construction"}, "objective": objective}


class _Controller:
    def __init__(self):
        self.calls = 0

    def evaluate_and_execute(self, objective):
        self.calls += 1
        return {"action": "activated_existing_factory", "objective": objective}


def test_evaluate_is_pure_and_does_not_activate():
    gateway = FactoryRuntimeAutonomyGateway()
    requirements = _Requirements()
    controller = _Controller()
    gateway.requirements = requirements
    gateway.controller = controller

    result = gateway.evaluate("autonomous objective")

    assert result["decision"]["action"] == "route_to_construction"
    assert requirements.calls == 1
    assert controller.calls == 0
