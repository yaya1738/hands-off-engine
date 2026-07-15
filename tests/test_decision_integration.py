from ai.factory.decision_integration import (
    FactoryDecisionIntegration,
)


class FakeOptimizer:
    def analyze(self):
        return {
            "analyzed": True,
        }


def fake_router(decision):
    return {
        "routed": True,
    }


def build():
    return FactoryDecisionIntegration(
        optimizer=FakeOptimizer(),
        router=fake_router,
    )


def test_evaluate():
    decision = build()

    result = decision.evaluate()

    assert result["analyzed"] is True


def test_select():
    decision = build()

    result = decision.select(
        [
            {
                "action": "OPTIMIZE",
            }
        ]
    )

    assert result["selected"]["action"] == "OPTIMIZE"


def test_route():
    decision = build()

    result = decision.route({})

    assert result["routed"] is True


def test_history():
    decision = build()

    decision.evaluate()

    assert len(decision.history()) == 1
