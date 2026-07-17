from typing import Any, Dict, List


class FactoryDevelopmentPipeline:
    def __init__(
        self,
        advisor=None,
        approval=None,
    ):
        self.advisor = advisor
        self.approval = approval
        self._history: List[Dict[str, Any]] = []

    def process(
        self,
        findings: Dict[str, Any],
    ):
        recommendations = self.advisor.analyze(
            findings
        )

        proposals = []

        for item in recommendations.get(
            "recommendations",
            [],
        ):
            proposal = {
                "type": item["type"],
                "target": item["target"],
                "risk": item["risk"],
                "requires_approval": item["requires_approval"],
                "status": "pending_approval",
            }

            if self.approval:
                proposal = self.approval.request(
                    proposal
                )

            proposals.append(proposal)

        result = {
            "proposals": proposals,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
