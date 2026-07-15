from typing import Any, Dict


class FactoryDaemonScheduler:
    def __init__(
        self,
        daemon: Any,
        scheduler: Any,
    ):
        self.daemon = daemon
        self.scheduler = scheduler

    def run_cycle(self) -> Dict[str, Any]:
        if not self.daemon.status()["running"]:
            return {
                "status": "inactive",
            }

        jobs = self.scheduler.run_pending()

        return {
            "status": "active",
            "jobs": jobs,
        }

    def tick(self):
        return self.run_cycle()

    def status(self):
        return {
            "daemon": self.daemon.status(),
            "jobs": self.scheduler.list_jobs(),
        }
