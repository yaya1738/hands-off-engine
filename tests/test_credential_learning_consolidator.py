from autonomous.credentials.intelligence.learning_consolidator import (
    IntelligenceLearningConsolidator,
)


def test_learning():

    result = IntelligenceLearningConsolidator().consolidate(
        {
            "accuracy": True,
            "confidence_update": 0.85,
        }
    )

    assert result["learning_event"] == "forecast_confirmed"
    assert result["accuracy"] == 1.0
    assert result["memory_updated"] is True
    assert result["mode"] == "read_only"
