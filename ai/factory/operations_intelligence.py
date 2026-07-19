from typing import Any, Dict, List


class FactoryOperationsIntelligence:
    def __init__(self, factory):
        self.factory = factory

    def system_loop_status(self) -> Dict[str, bool]:
        return {
            "assessment": hasattr(self.factory, "improvement_assessment"),
            "planner": hasattr(self.factory, "improvement_planner"),
            "approval": hasattr(self.factory, "improvement_approval"),
            "decision": hasattr(self.factory, "decision_option_adapter"),
            "resolver": hasattr(self.factory, "improvement_action_resolver"),
            "executor": hasattr(self.factory, "improvement_executor"),
            "audit": hasattr(self.factory, "improvement_audit"),
        }

    def capability_status(self) -> Dict[str, Any]:
        resolver = getattr(
            self.factory,
            "improvement_action_resolver",
            None,
        )

        registered = []

        if resolver and hasattr(resolver, "_actions"):
            registered = list(
                resolver._actions.keys()
            )

        return {
            "registered_count": len(registered),
            "registered": registered,
        }

    def generate_report(self) -> Dict[str, Any]:
        capabilities = self.capability_status()

        gaps: List[str] = []

        if capabilities["registered_count"] == 0:
            gaps.append(
                "no registered improvement capabilities"
            )

        return {
            "system_loop": self.system_loop_status(),
            "capabilities": capabilities,
            "gaps": gaps,
        }
