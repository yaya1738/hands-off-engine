from typing import Any, Dict, List


class FactoryImprovementDesignGenerator:

    def __init__(self):
        self._history = []

    def _generate_responsibilities(
        self,
        name: str,
        problem: str,
        data_requirements: List[str],
        integration_points: List[str],
        verification_criteria: List[str],
    ):
        name_lower = name.lower()
        problem_lower = problem.lower()

        responsibilities = []

        context = " ".join(
            data_requirements
            + integration_points
            + verification_criteria
        ).lower()

        if "architecture" in name_lower or "context" in name_lower:
            responsibilities.extend([
                "collect architecture metadata",
                "map component relationships",
                "identify integration boundaries",
            ])

        if "responsibility" in name_lower or "specification" in name_lower:
            responsibilities.extend([
                "translate capability intent into engineering duties",
                "define operational component responsibilities",
                "map responsibilities to interfaces and dependencies",
            ])

        if "overlap" in name_lower or "duplicate" in name_lower:
            responsibilities.extend([
                "compare requested capabilities against existing components",
                "identify reuse opportunities",
                "prevent redundant implementations",
            ])

        if "routing" in name_lower or "execution" in name_lower:
            responsibilities.extend([
                "map specifications to implementation paths",
                "track implementation progress",
                "connect execution outcomes to verification",
            ])

        if "verification" in context or "validation" in context or "validation" in problem_lower:
            responsibilities.append(
                "define verification obligations"
            )

        if not responsibilities and (data_requirements or integration_points):
            responsibilities.extend([
                "analyze capability intent",
                "derive component behavior",
                "map inputs and outputs",
                "integrate with Factory workflows",
                "support verification",
            ])

        if not responsibilities:
            responsibilities.extend([
                "provide capability",
                "integrate with Factory",
                "support verification",
            ])

        return responsibilities

    def generate_specification(
        self,
        improvement_name: str,
        purpose: str,
        responsibilities: List[str],
        dependencies: List[str],
        category: str = "factory_capability",
        problem: str = "",
        interfaces: List[str] = None,
        integration_points: List[str] = None,
        data_requirements: List[str] = None,
        verification_criteria: List[str] = None,
        failure_modes: List[str] = None,
    ):

        interfaces = interfaces or []
        integration_points = integration_points or []
        data_requirements = data_requirements or []
        verification_criteria = verification_criteria or []
        failure_modes = failure_modes or []

        synthesized = self._generate_responsibilities(
            improvement_name,
            problem,
            data_requirements,
            integration_points,
            verification_criteria,
        )

        specification = {
            "name": improvement_name,
            "category": category,
            "problem": problem,
            "purpose": purpose,
            "responsibilities": synthesized,
            "interfaces": interfaces,
            "dependencies": dependencies,
            "integration_points": integration_points,
            "data_requirements": data_requirements,
            "verification_criteria": verification_criteria,
            "failure_modes": failure_modes,
            "status": "SPECIFICATION_CREATED",
        }

        self._history.append(specification)

        return {
            "generated": True,
            "specification": specification,
        }

    def history(self):
        return self._history
