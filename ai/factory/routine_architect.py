from typing import Any, Dict, List


class FactoryRoutineArchitect:
    def __init__(self):
        self._designs: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def analyze_requirement(
        self,
        requirement: str,
    ):
        return {
            "requirement": requirement,
            "analyzed": True,
        }

    def design_routine(
        self,
        name: str,
        purpose: str,
        steps: List[str],
        dependencies: List[str] | None = None,
    ):
        routine = {
            "name": name,
            "purpose": purpose,
            "steps": steps,
            "dependencies": dependencies or [],
            "status": "DESIGNED",
        }

        self._designs[name] = routine
        self._history.append(routine)

        return {
            "designed": True,
            "routine": routine,
        }

    def generate_definition(
        self,
        name: str,
    ):
        routine = self._designs.get(name)

        if not routine:
            return {
                "generated": False,
                "reason": "NOT_FOUND",
            }

        return {
            "generated": True,
            "definition": routine,
        }

    def validate_definition(
        self,
        name: str,
    ):
        routine = self._designs.get(name)

        if not routine:
            return {
                "valid": False,
                "reason": "NOT_FOUND",
            }

        valid = bool(
            routine["name"]
            and routine["purpose"]
            and routine["steps"]
        )

        return {
            "valid": valid,
            "routine": name,
        }

    def history(self):
        return self._history
