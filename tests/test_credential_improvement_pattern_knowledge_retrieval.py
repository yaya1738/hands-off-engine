from autonomous.credentials.intelligence.improvement_pattern_knowledge_retrieval import (
    IntelligenceImprovementPatternKnowledgeRetrieval,
)


def test_retrieval():

    result = IntelligenceImprovementPatternKnowledgeRetrieval().retrieve(
        "pattern_feedback_consolidated",
        [
            {
                "learning_event":
                "pattern_feedback_consolidated",
                "reliability": 1.0,
            }
        ],
    )

    assert result["query"] == (
        "pattern_feedback_consolidated"
    )
    assert result["matches"] == 1
    assert result["reliability"] == 1.0
    assert result["mode"] == "read_only"
