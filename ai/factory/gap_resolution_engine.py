from typing import Any, Dict, List


class FactoryGapResolutionEngine:
    def __init__(self):
        self._analyses: List[Dict[str, Any]] = []

    def analyze_state(
        self,
        current_capabilities: List[str],
    ):
        return {
            "current_capabilities": current_capabilities,
            "analyzed": True,
        }

    def compare_target(
        self,
        current_capabilities: List[str],
        desired_capabilities: List[str],
    ):
        missing = [
            item
            for item in desired_capabilities
            if item not in current_capabilities
        ]

        return {
            "missing": missing,
            "complete": len(missing) == 0,
        }

    def identify_gap(
        self,
        current_capabilities: List[str],
        desired_capabilities: List[str],
        workflow_issue: str,
    ):
        comparison = self.compare_target(
            current_capabilities,
            desired_capabilities,
        )

        gap = {
            "workflow_issue": workflow_issue,
            "missing_capabilities": comparison["missing"],
            "gap_identified": not comparison["complete"],
        }

        return gap

    def generate_component_request(
        self,
        name: str,
        purpose: str,
        responsibilities: List[str],
    ):
        request = {
            "component_name": name,
            "purpose": purpose,
            "responsibilities": responsibilities,
            "status": "REQUESTED",
        }

        self._analyses.append(request)

        return {
            "generated": True,
            "request": request,
        }

    def history(self):
        return self._analyses
