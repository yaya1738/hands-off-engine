from typing import Any, Dict, List


class ProvisioningAuditSummary:
    def summarize(
        self,
        records: List[Any],
        integrity_results: List[Any] = None,
        consistency_results: List[Any] = None,
    ) -> Dict[str, Any]:
        integrity_results = integrity_results or []
        consistency_results = consistency_results or []

        decisions = {
            "AUDIT_ONLY": 0,
            "DENY": 0,
            "APPROVAL_QUEUE": 0,
        }

        issues = []

        for record in records:
            decision = getattr(record, "decision", None)

            if decision in decisions:
                decisions[decision] += 1

        for result in integrity_results:
            if not getattr(result, "valid", True):
                issues.extend(getattr(result, "issues", []))

        for result in consistency_results:
            if not getattr(result, "valid", True):
                issues.extend(getattr(result, "issues", []))

        return {
            "total_records": len(records),
            "valid_records": len(records) - len(issues),
            "invalid_records": len(issues),
            "decisions": decisions,
            "issues": issues,
        }
