class ImpactRankingEngine:

    def rank(self, pattern):

        occurrences = pattern.get(
            "occurrences",
            0
        )

        identities = pattern.get(
            "identity_count",
            0
        )

        score = (
            occurrences * 10
            +
            identities * 15
        )

        score = min(
            100,
            score
        )

        if score >= 70:
            severity = "high"
        elif score >= 40:
            severity = "medium"
        else:
            severity = "low"

        return {
            "pattern":
            pattern.get("diagnosis"),

            "priority":
            score,

            "severity":
            severity,

            "mode":
            "read_only",
        }
