from ai.factory.intelligence_coordinator import (
    FactoryIntelligenceCoordinator,
)


class FakeKnowledge:
    def retrieve_context(self):
        return {
            "context": [
                {}
            ],
        }


class FakeDecision:
    def evaluate(self):
        return {
            "decision": "OPTIMIZE",
        }


class FakeImprovement:
    def execute(self):
        return {
            "status": "EXECUTED",
        }


class FakeEvolution:
    def apply(self, change):
        return {
            "status": "APPLIED",
        }


def build():
    return FactoryIntelligenceCoordinator(
        knowledge=FakeKnowledge(),
        decision=FakeDecision(),
        improvement=FakeImprovement(),
        evolution=FakeEvolution(),
    )


def test_observe():
    coordinator = build()

    result = coordinator.observe()

    assert result["observed"] is True


def test_analyze():
    coordinator = build()

    result = coordinator.analyze()

    assert len(result["context"]) == 1


def test_decide():
    coordinator = build()

    result = coordinator.decide()

    assert result["decision"] == "OPTIMIZE"


def test_improve():
    coordinator = build()

    result = coordinator.improve()

    assert result["status"] == "EXECUTED"


def test_evolve():
    coordinator = build()

    result = coordinator.evolve()

    assert result["status"] == "APPLIED"


def test_history():
    coordinator = build()

    coordinator.observe()

    assert len(coordinator.history()) == 1
