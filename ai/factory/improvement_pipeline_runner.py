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


class FactoryImprovementPipelineRunner:
    def __init__(self):
        self.assessor = FactoryCapabilityAssessmentRunner()
        self.roadmap = FactoryRuntimeRoadmapGenerator()
        self.designer = FactoryImprovementDesignGenerator()
        self.bridge = FactorySpecificationDevelopmentBridge()
        self._history: List[Dict[str, Any]] = []

    def run(
        self,
        name: str,
        current_capabilities: List[str],
        desired_capabilities: List[str],
        objective: str,
    ):
        assessment = self.assessor.run_assessment(
            name,
            current_capabilities,
            desired_capabilities,
            objective,
        )

        roadmap = self.roadmap.generate(
            assessment
        )

        top_improvement = (
            roadmap["roadmap"]["ranked_improvements"][0]
        )

        specification = self.designer.generate_specification(
            top_improvement,
            f"Implement missing capability: {top_improvement}",
            [
                "provide capability",
                "integrate with runtime",
                "support verification",
            ],
            current_capabilities,
        )

        development = self.bridge.create_development_request(
            specification["specification"]
        )

        result = {
            "assessment": assessment,
            "roadmap": roadmap,
            "specification": specification,
            "development_request": development,
            "status": "COMPLETE",
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
