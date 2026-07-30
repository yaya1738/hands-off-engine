from typing import Any, Dict, List


class FactorySystemArchitect:
    def __init__(self):
        self._designs: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def analyze_need(
        self,
        need: str,
    ):
        return {
            "need": need,
            "analyzed": True,
        }

    def design_system(
        self,
        name: str,
        purpose: str,
        components: List[str],
        dependencies: List[str] | None = None,
    ):
        design = {
            "name": name,
            "purpose": purpose,
            "components": components,
            "dependencies": dependencies or [],
            "status": "DESIGNED",
        }

        self._designs[name] = design
        self._history.append(design)

        return {
            "designed": True,
            "system": design,
        }

    def generate_plan(
        self,
        name: str,
    ):
        design = self._designs.get(name)

        if not design:
            return {
                "generated": False,
                "reason": "NOT_FOUND",
            }

        return {
            "generated": True,
            "plan": design,
        }

    def validate_design(
        self,
        name: str,
    ):
        design = self._designs.get(name)

        if not design:
            return {
                "valid": False,
                "reason": "NOT_FOUND",
            }

        return {
            "valid": bool(
                design["name"]
                and design["purpose"]
                and design["components"]
            ),
            "system": name,
        }

    def history(self):
        return self._history
