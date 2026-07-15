class IntelligenceReportGenerator:

    def generate(
        self,
        health,
        stability,
        score,
        gate,
    ):

        return {
            "system": "credential_bridge",
            "status": health,
            "intelligence": {
                "score": score,
                "gate": gate,
            },
            "risk": {
                "health": health,
                "stability": stability,
            },
            "mode": "read_only",
        }
