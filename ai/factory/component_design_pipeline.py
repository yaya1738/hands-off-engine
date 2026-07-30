from typing import Any, Dict, List

from ai.factory.component_design_engine import (
    FactoryComponentDesignEngine,
)


class FactoryComponentDesignPipeline:
    def __init__(self):
        self.engine = FactoryComponentDesignEngine()
        self._history: List[Dict[str, Any]] = []

    def submit_design_request(
        self,
        need: str,
        current_capabilities: List[str],
        desired_outcome: str,
        component_name: str,
        purpose: str,
        responsibilities: List[str],
        dependencies: List[str] | None = None,
    ):
        analysis = self.engine.analyze_need(
            need,
        )

        gap = self.engine.identify_missing_layer(
            current_capabilities,
            desired_outcome,
        )

        design = self.engine.design_component(
            component_name,
            purpose,
            responsibilities,
            dependencies or [],
        )

        validation = self.engine.validate_design(
            component_name,
        )

        result = {
            "analysis": analysis,
            "gap": gap,
            "design": design,
            "validation": validation,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
