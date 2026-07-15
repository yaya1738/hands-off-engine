from ai.factory.optimization_feedback import (
    FactoryOptimizationFeedback,
)


class FakeMetrics:
    def snapshot(self):
        return {
            "cycles": 10,
            "successes": 9,
        }


def build():
    return FactoryOptimizationFeedback(
        FakeMetrics()
    )


def test_analyze():
    feedback = build()

    result = feedback.analyze()

    assert result["analyzed"] is True


def test_recommend():
    feedback = build()

    result = feedback.recommend()

    assert result["recommendation"] == "OPTIMIZE"


def test_apply_feedback():
    feedback = build()

    result = feedback.apply_feedback()

    assert result["status"] == "APPLIED"


def test_history():
    feedback = build()

    feedback.analyze()

    assert len(feedback.history()) == 1
