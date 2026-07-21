from typing import Any, Dict, List


class FactoryActionRouter:
    def __init__(
        self,
        recovery=None,
        improvement=None,
    ):
        self.recovery = recovery
        self.improvement = improvement
        self._history: List[Dict[str, Any]] = []

    def route(
        self,
        decision: Dict[str, Any],
    ):
        action = decision.get(
            "decision"
        )

        if action == "RECOVER":
            target = "runtime_recovery"

        elif action == "IMPROVE":
            target = "improvement_pipeline"

        else:
            capability_context = decision.get(
                "capability_context",
                {}
            )

            if "self_improvement" in str(capability_context):
                target = "improvement_pipeline"
            else:
                target = "continue"

        result = {
            "decision": action,
            "action": target,
            "capability_context": decision.get(
                "capability_context",
                {}
            ),
        }

        self._history.append(
            result
        )

        return result

    def execute(
        self,
        routed: Dict[str, Any],
    ):
        action = routed.get(
            "action"
        )

        if action == "runtime_recovery":
            if self.recovery:
                return self.recovery.recover(
                    {
                        "level": "CRITICAL",
                    }
                )

        if action == "improvement_pipeline":
            if self.improvement:
                return self.improvement()

        return {
            "status": "NO_ACTION",
        }

    def history(self):
        return self._history
