from typing import Any, Dict, List


class FactoryRuntimeScheduler:
    def __init__(
        self,
        executor=None,
    ):
        self.executor = executor
        self.paused = False
        self._queue: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def schedule(
        self,
        task: Dict[str, Any],
    ):
        self._queue.append(
            task
        )

        result = {
            "status": "SCHEDULED",
            "task": task,
        }

        self._history.append(
            result
        )

        return result

    def run_pending(self):
        if self.paused:
            return {
                "status": "PAUSED",
            }

        results = []

        while self._queue:
            task = self._queue.pop(0)

            if self.executor:
                result = self.executor(task)

            else:
                result = {
                    "status": "NO_EXECUTOR",
                }

            results.append(result)

        output = {
            "status": "COMPLETED",
            "results": results,
        }

        self._history.append(
            output
        )

        return output

    def pause(self):
        self.paused = True

        result = {
            "status": "PAUSED",
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
