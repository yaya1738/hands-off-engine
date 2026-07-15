from typing import Any


class FactoryEventIntegration:
    def __init__(
        self,
        event_bus: Any,
    ):
        self.event_bus = event_bus

    def emit_job_event(
        self,
        job_id: str,
        status: str,
        output=None,
    ):
        return self.event_bus.publish(
            "JOB_COMPLETED",
            {
                "job_id": job_id,
                "status": status,
                "output": output,
            },
        )

    def emit_decision_event(
        self,
        decision: str,
        confidence: float = 0,
    ):
        return self.event_bus.publish(
            "DECISION_MADE",
            {
                "decision": decision,
                "confidence": confidence,
            },
        )

    def emit_action_event(
        self,
        action: str,
        result=None,
    ):
        return self.event_bus.publish(
            "ACTION_EXECUTED",
            {
                "action": action,
                "result": result,
            },
        )
