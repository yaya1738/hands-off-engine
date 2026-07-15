from typing import Any, Callable, Dict


class FactoryJobExecutor:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register_handler(
        self,
        job_type: str,
        handler: Callable,
    ) -> None:
        self._handlers[job_type] = handler

    def execute(
        self,
        job_type: str,
        payload: Any = None,
    ):
        handler = self._handlers.get(job_type)

        if not handler:
            return {
                "error": "unknown_job",
                "job_type": job_type,
            }

        return handler(payload)

    def available_jobs(self):
        return list(self._handlers.keys())
