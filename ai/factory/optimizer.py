from typing import Any, Dict


class FactoryOptimizer:
    def __init__(
        self,
        decision_engine: Any,
        policy_gate: Any,
    ):
        self.decision_engine = decision_engine
        self.policy_gate = policy_gate

    def run_cycle(
        self,
        health: Dict[str, Any],
        history: list,
        telemetry: Dict[str, Any],
    ) -> Dict[str, Any]:

        decision = self.decision_engine.analyze(
            health,
            history,
            telemetry,
        )

        policy = self.policy_gate.evaluate(
            decision,
        )

        return {
            "decision": decision,
            "policy": policy,
        }
