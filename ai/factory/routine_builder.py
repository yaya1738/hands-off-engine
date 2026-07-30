from typing import Any, Dict, List


class FactoryRoutineBuilder:
    def __init__(self):
        self._routines: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def create_routine(
        self,
        name: str,
        purpose: str,
        steps: List[str],
    ):
        routine = {
            "name": name,
            "purpose": purpose,
            "steps": steps,
            "status": "CREATED",
        }

        self._routines[name] = routine
        self._history.append(routine)

        return {
            "created": True,
            "routine": routine,
        }

    def register_routine(
        self,
        routine: Dict[str, Any],
    ):
        name = routine["name"]

        self._routines[name] = routine
        self._history.append(routine)

        return {
            "registered": True,
            "routine": name,
        }

    def execute_routine(
        self,
        name: str,
    ):
        routine = self._routines.get(name)

        if not routine:
            return {
                "executed": False,
                "reason": "NOT_FOUND",
            }

        return {
            "executed": True,
            "routine": name,
            "steps": routine["steps"],
        }

    def verify_routine(
        self,
        name: str,
    ):
        routine = self._routines.get(name)

        if not routine:
            return {
                "verified": False,
                "reason": "NOT_FOUND",
            }

        return {
            "verified": True,
            "routine": name,
            "step_count": len(routine["steps"]),
        }

    def history(self):
        return self._history
