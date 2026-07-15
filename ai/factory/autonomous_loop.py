from typing import Any, Dict, List


class FactoryAutonomousLoop:
    def __init__(
        self,
        observer=None,
        decision_engine=None,
        router=None,
    ):
        self.observer = observer
        self.decision_engine = decision_engine
        self.router = router
        self._history: List[Dict[str, Any]] = []

    def observe(
        self,
        state: Dict[str, Any],
    ):
        if self.observer:
            return self.observer(state)

        return state

    def decide(
        self,
        observation: Dict[str, Any],
    ):
        return self.decision_engine.decide(
            observation
        )

    def act(
        self,
        decision: Dict[str, Any],
    ):
        routed = self.router.route(
            decision
        )

        result = self.router.execute(
            routed
        )

        return {
            "route": routed,
            "result": result,
        }

    def run_cycle(
        self,
        state: Dict[str, Any],
    ):
        observation = self.observe(
            state
        )

        decision = self.decide(
            observation
        )

        action = self.act(
            decision
        )

        result = {
            "observation": observation,
            "decision": decision,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
