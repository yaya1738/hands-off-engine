from autonomous.credentials.intelligence.improvement_pattern_memory_summarizer import (
    IntelligenceImprovementPatternMemorySummarizer,
)


def test_summary():

    result = IntelligenceImprovementPatternMemorySummarizer().summarize(
        [
            {
                "pattern":
                "prioritize_pattern_feedback_learning",
                "score":
                0.85,
            }
        ]
    )

    assert result["summary"] == (
        "prioritize_pattern_feedback_learning"
    )
    assert result["confidence"] == 0.85
    assert result["mode"] == "read_only"
