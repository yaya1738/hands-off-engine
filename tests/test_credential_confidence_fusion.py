from autonomous.credentials.intelligence.confidence_fusion import (
    ConfidenceFusion,
)


def test_confidence_fusion():

    result = ConfidenceFusion().calculate(
        0.66,
        1.0,
        1.0,
    )

    assert result["confidence"] == 0.83
    assert result["mode"] == "read_only"
