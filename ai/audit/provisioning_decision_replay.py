from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ReplayResult:
    replayed_decision: str
    matches_original: bool
    difference_report: Dict[str, Any]


class ProvisioningDecisionReplay:
    def replay(
        self,
        original_decision: str,
        replayed_decision: str,
    ) -> ReplayResult:
        return ReplayResult(
            replayed_decision=replayed_decision,
            matches_original=(
                original_decision == replayed_decision
            ),
            difference_report={
                "original": original_decision,
                "replayed": replayed_decision,
            },
        )
