class FactoryCapabilityEvolutionDecision:

    def decide(
        self,
        gap_analysis,
        consolidation,
    ):

        missing = gap_analysis.get(
            "missing_capabilities",
            []
        )

        if missing:
            return {
                "decision": "CREATE_IMPROVEMENT_PROPOSAL",
                "missing_capabilities": missing,
            }

        archived = consolidation.get(
            "archived_candidates",
            []
        )

        if archived:
            return {
                "decision": "PRESERVE_CONSOLIDATION",
                "archived_candidates": archived,
            }

        return {
            "decision": "NO_CAPABILITY_CHANGE_REQUIRED",
        }
