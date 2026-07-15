from ai.factory.decision_feedback import (
    FactoryDecisionFeedback,
)


def test_record_decision():
    system = FactoryDecisionFeedback()

    result = system.record_decision(
        {
            "action": "restart_worker",
        }
    )

    assert result["outcome"] is None


def test_record_outcome():
    system = FactoryDecisionFeedback()

    entry = system.record_decision(
        {
            "action": "restart_worker",
        }
    )

    result = system.record_outcome(
        entry,
        {
            "success": True,
            "impact": 0.5,
        },
    )

    assert result["outcome"]["success"] is True


def test_evaluate_success():
    system = FactoryDecisionFeedback()

    entry = system.record_decision(
        {
            "action": "fix",
        }
    )

    system.record_outcome(
        entry,
        {
            "success": True,
            "impact": 1,
        },
    )

    result = system.evaluate(
        entry
    )

    assert result["status"] == "IMPROVED"


def test_history():
    system = FactoryDecisionFeedback()

    system.record_decision(
        {}
    )

    assert len(system.history()) == 1
