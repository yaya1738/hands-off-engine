class DigestOrchestrator:

    def build(
        self,
        diagnosis,
        confidence,
        priority,
        recommendation,
        evidence=None,
        history=None,
    ):

        return {
            "system": "credential_bridge",
            "status": (
                "attention_required"
                if priority >= 80
                else "healthy"
            ),
            "diagnosis": diagnosis,
            "confidence": confidence,
            "priority": priority,
            "recommendation": recommendation,
            "evidence": evidence or [],
            "history": history or {},
            "safety": {
                "oauth_execution": False,
                "state_change": False,
                "auto_repair": False,
                "credential_actions": False,
            },
            "mode": "read_only",
        }
