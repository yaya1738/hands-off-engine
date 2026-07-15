class IntelligenceStabilityScorer:

    def score(self, drift):

        changes = len(
            drift.get(
                "changes",
                []
            )
        )

        if changes == 0:
            return {
                "stability_score":
                    1.0,
                "status":
                    "stable",
                "drift_events":
                    0,
                "mode":
                    "read_only",
            }

        if changes == 1:
            return {
                "stability_score":
                    0.72,
                "status":
                    "minor_variation",
                "drift_events":
                    changes,
                "mode":
                    "read_only",
            }

        return {
            "stability_score":
                0.4,
            "status":
                "unstable",
            "drift_events":
                changes,
            "mode":
                "read_only",
        }
