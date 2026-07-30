from typing import Any, Dict


class FactoryCapabilityEvolutionContext:
    def build(
        self,
        gap_analysis: Dict[str, Any],
        consolidation: Dict[str, Any],
        evolution_decision: Dict[str, Any],
    ):
        decision = evolution_decision.get(
            "decision",
            "NO_CAPABILITY_CHANGE_REQUIRED",
        )

        return {
            "mode": decision,
            "capability_state": {
                "missing_capabilities": gap_analysis.get(
                    "missing_capabilities",
                    [],
                ),
                "archived_candidates": consolidation.get(
                    "archived_candidates",
                    [],
                ),
            },
            "allowed_actions": self.allowed_actions(
                decision
            ),
            "blocked_actions": self.blocked_actions(
                decision
            ),
        }

    def allowed_actions(self, decision):
        if decision == "CREATE_IMPROVEMENT_PROPOSAL":
            return [
                "create_capability",
                "repair_gap",
                "improve_existing_capability",
            ]

        if decision == "PRESERVE_CONSOLIDATION":
            return [
                "optimize_existing_capability",
                "repair_integration",
            ]

        return [
            "maintain_current_capabilities",
        ]

    def blocked_actions(self, decision):
        if decision == "PRESERVE_CONSOLIDATION":
            return [
                "duplicate_capability_creation",
            ]

        return []
