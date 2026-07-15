from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class IntegrityResult:
    valid: bool
    checks: Dict[str, bool]
    issues: List[str]


class ProvisioningIntegrityVerifier:
    def verify(self, record: Any) -> IntegrityResult:
        checks = {
            "policy_hash_present": bool(getattr(record, "policy_hash", None)),
            "evidence_present": bool(getattr(record, "evidence", None)),
            "replay_consistent": getattr(record, "replay_match", False) is True,
            "required_fields_present": all(
                [
                    getattr(record, "decision_id", None),
                    getattr(record, "request_id", None),
                    getattr(record, "decision", None),
                ]
            ),
        }

        issues = [
            name for name, passed in checks.items()
            if not passed
        ]

        return IntegrityResult(
            valid=len(issues) == 0,
            checks=checks,
            issues=issues,
        )
