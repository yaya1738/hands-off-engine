class RecommendationEngine:

    def recommend(
        self,
        diagnosis,
        confidence,
        evidence=None,
    ):

        if diagnosis == "authorization_consent_required":
            recommendation = "await_user_authorization"
            priority = 100

        elif diagnosis == "no_known_anomaly":
            recommendation = "continue_monitoring"
            priority = 10

        else:
            recommendation = "investigate"
            priority = 50

        return {
            "diagnosis": diagnosis,
            "recommendation": recommendation,
            "priority": priority,
            "confidence": confidence,
            "evidence": evidence or [],
            "mode": "read_only",
        }
