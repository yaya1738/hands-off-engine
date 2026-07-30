from typing import Any, Dict, List

from ai.factory.capability_assessment_runner import (
    FactoryCapabilityAssessmentRunner,
)

from ai.factory.runtime_roadmap_generator import (
    FactoryRuntimeRoadmapGenerator,
)

from ai.factory.improvement_design_generator import (
    FactoryImprovementDesignGenerator,
)

from ai.factory.specification_development_bridge import (
    FactorySpecificationDevelopmentBridge,
)


class FactoryDevelopmentEntryPoint:
    def __init__(self):
        self.assessment = FactoryCapabilityAssessmentRunner()
        self.roadmap = FactoryRuntimeRoadmapGenerator()
        self.design = FactoryImprovementDesignGenerator()
        self.bridge = FactorySpecificationDevelopmentBridge()
        self._history = []

    def submit_objective(
        self,
        objective: str,
        current_capabilities: List[str],
        desired_capabilities: List[str],
        architecture_context: Dict[str, Any] = None,
    ):

        architecture_context = architecture_context or {}

        assessment = self.assessment.run_assessment(
            objective,
            current_capabilities,
            desired_capabilities,
            objective,
        )

        roadmap = self.roadmap.generate(
            assessment
        )

        target = (
            roadmap["roadmap"]["ranked_improvements"][0]
        )

        specification = self.design.generate_specification(
            target,
            f"Implement capability: {target}",
            [
                "provide capability",
                "integrate with Factory",
                "support verification",
            ],
            current_capabilities,
            problem=(
                f"Identified improvement from objective: "
                f"{objective}"
            ),
            integration_points=architecture_context.get(
                "integration_points",
                [],
            ),
            interfaces=architecture_context.get(
                "interfaces",
                [],
            ),
            data_requirements=architecture_context.get(
                "data_requirements",
                [],
            ),
            verification_criteria=architecture_context.get(
                "verification_patterns",
                [],
            ),
        )

        development_request = (
            self.bridge.create_development_request(
                specification["specification"]
            )
        )

        result = {
            "objective": objective,
            "assessment": assessment,
            "roadmap": roadmap,
            "specification": specification,
            "development_request": development_request,
            "architecture_context": architecture_context,
            "status": "COMPLETE",
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
