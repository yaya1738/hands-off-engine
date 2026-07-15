from autonomous.credentials.intelligence.context_enhancer import (
    IntelligenceContextEnhancer,
)


def test_context():

    result = IntelligenceContextEnhancer().enhance(
        "authorization_consent_required",
        0.69,
        0.81,
    )

    assert result["confidence_delta"] == -0.12
    assert result["context_quality"] == "confidence_decline"
    assert result["mode"] == "read_only"
