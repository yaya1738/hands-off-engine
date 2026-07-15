class IntelligenceDigestComposer:

    def compose(
        self,
        diagnosis,
        confidence,
        evidence,
        context,
        impact
    ):

        return {
            "diagnosis": diagnosis,
            "confidence": confidence,
            "evidence": evidence,
            "context": context,
            "impact": impact,
            "mode": "read_only",
        }
