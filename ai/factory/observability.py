from typing import Any, Dict


class FactoryObservability:
    def __init__(
        self,
        daemon: Any = None,
        metrics: Any = None,
        audit: Any = None,
        events: Any = None,
    ):
        self.daemon = daemon
        self.metrics = metrics
        self.audit = audit
        self.events = events

    def health(self):
        if self.daemon:
            return self.daemon.status()

        return {
            "status": "unknown",
        }

    def snapshot(
        self,
        job_results=None,
    ) -> Dict[str, Any]:

        result = {
            "health": self.health(),
        }

        if self.metrics and job_results is not None:
            result["metrics"] = (
                self.metrics.calculate(
                    job_results
                )
            )

        if self.audit:
            result["audit_events"] = (
                self.audit.list_events()
            )

        if self.events:
            result["events"] = (
                self.events.history()
            )

        return result

    def report(
        self,
        job_results=None,
    ):
        return self.snapshot(
            job_results
        )
