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
        self.actions = {}


    def register_action(
        self,
        name,
        handler,
    ):
        self.actions[name] = handler

        return {
            "registered": True,
            "action": name,
        }


    def route(
        self,
        decision: Dict[str, Any],
    ):
        action = decision.get(
            "decision"
        )

        if action == "CONTINUE":
            result = {
                "decision": action,
                "action": "continue",
            }

            if action in self.actions:
                result["result"] = self.actions[action]()

            self._history.append(result)

            return result

        if action == "RECOVER":
            target = "runtime_recovery"

        elif action == "IMPROVE":
            target = "improvement_pipeline"

        else:
            if (
                action not in self.actions
                and action not in {
                    None,
                    "RECOVER",
                    "IMPROVE",
                }
            ):
                result = {
                    "error": "unknown_action",
                    "decision": action,
                }

                self._history.append(result)

                return result

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

        if action in self.actions:
            result["result"] = self.actions[action]()

        if action in self.actions and "result" not in result:
            result["result"] = self.actions[action]()

        if action in self.actions and "result" not in result:
            result["result"] = self.actions[action]()

        if action in self.actions and "result" not in result:
            result["result"] = self.actions[action]()

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
