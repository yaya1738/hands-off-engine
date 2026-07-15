class CredentialHealthScorer:

    def score(self, metrics):

        score = 100

        score -= metrics.get("recovery_events", 0) * 5

        if score < 0:
            score = 0

        return {
            "health_score": score,
            "risk":
                "LOW" if score >= 80 else
                "MEDIUM" if score >= 50 else
                "HIGH"
        }
