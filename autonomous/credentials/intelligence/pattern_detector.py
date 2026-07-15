class IntelligencePatternDetector:

    def detect(self, timeline):

        decisions = timeline.get("decisions", [])
        risks = timeline.get("risks", [])

        occurrences = len(decisions)

        if (
            "human_review_priority" in decisions
            and "high" in risks
        ):
            pattern = "repeated_high_risk_attention"
            confidence = 0.84

        else:
            pattern = "no_repeated_pattern"
            confidence = 0.5

        return {
            "pattern": pattern,
            "occurrences": occurrences,
            "confidence": confidence,
            "mode": "read_only",
        }
