from ai.factory.gap_resolution_engine import (
    FactoryGapResolutionEngine,
)


def test_gap_detection():

    engine = FactoryGapResolutionEngine()

    result = engine.identify_gap(
        [
            "design",
            "verification",
        ],
        [
            "design",
            "verification",
            "creation",
        ],
        "design output cannot reach creation",
    )

    assert result["gap_identified"] is True
    assert "creation" in result["missing_capabilities"]


def test_component_request():

    engine = FactoryGapResolutionEngine()

    result = engine.generate_component_request(
        "creation_handoff_pipeline",
        "connect designs to construction",
        [
            "accept specification",
            "route creation",
            "track result",
        ],
    )

    assert result["generated"] is True
