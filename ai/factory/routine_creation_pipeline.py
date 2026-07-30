from typing import Any, Dict, List

from ai.factory.routine_architect import FactoryRoutineArchitect
from ai.factory.routine_builder import FactoryRoutineBuilder


class FactoryRoutineCreationPipeline:
    def __init__(self):
        self.architect = FactoryRoutineArchitect()
        self.builder = FactoryRoutineBuilder()
        self._history: List[Dict[str, Any]] = []

    def create_from_requirement(
        self,
        requirement: str,
        name: str,
        purpose: str,
        steps: List[str],
        dependencies: List[str] | None = None,
    ):
        design = self.architect.design_routine(
            name,
            purpose,
            steps,
            dependencies or [],
        )

        definition = self.architect.generate_definition(
            name,
        )

        if not definition["generated"]:
            result = {
                "created": False,
                "stage": "design",
            }

            self._history.append(result)
            return result

        built = self.builder.create_routine(
            name,
            purpose,
            steps,
        )

        verification = self.architect.validate_definition(
            name,
        )

        result = {
            "created": built["created"],
            "requirement": requirement,
            "design": design,
            "build": built,
            "verification": verification,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
