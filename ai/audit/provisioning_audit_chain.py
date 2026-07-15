from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ChainValidationResult:
    valid: bool
    links_checked: int
    issues: List[str]


class ProvisioningAuditChain:
    def __init__(self):
        self._links: Dict[str, str] = {}

    def add_link(self, stage: str, identifier: str) -> None:
        self._links[stage] = identifier

    def get_chain(self) -> Dict[str, str]:
        return dict(self._links)

    def validate(self) -> ChainValidationResult:
        required = [
            "request",
            "provenance",
            "decision",
            "policy",
        ]

        issues = []

        for stage in required:
            if not self._links.get(stage):
                issues.append(f"missing_{stage}")

        return ChainValidationResult(
            valid=len(issues) == 0,
            links_checked=len(self._links),
            issues=issues,
        )
