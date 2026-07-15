from ai.factory.autonomous_loop import (
    FactoryAutonomousLoop,
)


class FakeDecision:
    def decide(self, state):
        return {
            "decision": "CONTINUE",
        }


class FakeRouter:
    def route(self, decision):
        return {
            "action": "continue",
        }

    def execute(self, routed):
        return {
            "status": "OK",
        }


def test_cycle():
    loop = FactoryAutonomousLoop(
        decision_engine=FakeDecision(),
        router=FakeRouter(),
    )

    result = loop.run_cycle(
        {
            "health": "GOOD",
        }
    )

    assert result["decision"]["decision"] == "CONTINUE"


def test_history():
    loop = FactoryAutonomousLoop(
        decision_engine=FakeDecision(),
        router=FakeRouter(),
    )

    loop.run_cycle({})

    assert len(loop.history()) == 1
