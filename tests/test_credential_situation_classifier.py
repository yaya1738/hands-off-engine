from autonomous.credentials.intelligence.situation_classifier import (
    SituationClassifier,
)


def test_situation():

    result = SituationClassifier().classify(
        {
            "correlation":
            "repeated_intelligence_signal",
            "severity":
            "medium",
        }
    )

    assert result["situation"] == "attention_required"
    assert result["mode"] == "read_only"
