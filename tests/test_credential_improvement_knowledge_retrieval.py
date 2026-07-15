from autonomous.credentials.intelligence.improvement_knowledge_retrieval import (
    IntelligenceImprovementKnowledgeRetrieval,
)


def test_retrieval():

    result = IntelligenceImprovementKnowledgeRetrieval().retrieve(
        [
            {
                "knowledge":
                "increase_pattern_confidence_tracking",
                "reliability": 1.0,
            }
        ],
        "increase_pattern_confidence_tracking",
    )

    assert result["matches"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
