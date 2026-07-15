from dataclasses import dataclass
from typing import Any, List


@dataclass
class ConsistencyResult:
    valid: bool
    checks: int
    issues: List[str]


class ProvisioningConsistencyChecker:
    def check(
        self,
        provenance: Any,
        decision: Any,
        policy: Any,
        export: Any,
    ) -> ConsistencyResult:
        issues = []
        checks = 0

        if provenance.get("request_id") != decision.get("request_id"):
            issues.append("request_id_mismatch")
        checks += 1

        if decision.get("policy_version") != policy.get("version"):
            issues.append("policy_version_mismatch")
        checks += 1

        if export.get("decision") != decision.get("decision"):
            issues.append("decision_mismatch")
        checks += 1

        return ConsistencyResult(
            valid=len(issues) == 0,
            checks=checks,
            issues=issues,
        )
