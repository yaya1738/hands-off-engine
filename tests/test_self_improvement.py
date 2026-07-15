from ai.factory.self_improvement import (
    FactorySelfImprovement,
)


class FakeFeedback:
    def analyze(self):
        return {
            "analyzed": True,
        }

    def recommend(self):
        return {
            "recommendation": "OPTIMIZE",
        }


def fake_executor():
    return {
        "status": "EXECUTED",
    }


def build():
    return FactorySelfImprovement(
        feedback=FakeFeedback(),
        executor=fake_executor,
    )


def test_evaluate():
    improvement = build()

    result = improvement.evaluate()

    assert result["analyzed"] is True


def test_plan():
    improvement = build()

    result = improvement.plan()

    assert result["recommendation"] == "OPTIMIZE"


def test_execute():
    improvement = build()

    result = improvement.execute()

    assert result["status"] == "EXECUTED"


def test_verify():
    improvement = build()

    result = improvement.verify()

    assert result["verified"] is True


def test_history():
    improvement = build()

    improvement.evaluate()

    assert len(improvement.history()) == 1
