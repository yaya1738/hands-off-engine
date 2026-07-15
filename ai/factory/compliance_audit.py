from typing import Any, Dict, List


class FactoryComplianceAudit:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.violations: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def record_action(
        self,
        action: Dict[str, Any],
    ):
        record = {
            "action": action,
            "status": "RECORDED",
        }

        self.records.append(
            record
        )

        self._history.append(
            record
        )

        return record

    def verify_compliance(
        self,
        action: Dict[str, Any],
    ):
        result = {
            "compliant": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def generate_report(self):
        result = {
            "records": len(
                self.records
            ),
            "violations": len(
                self.violations
            ),
        }

        self._history.append(
            result
        )

        return result

    def flag_violation(
        self,
        action: Dict[str, Any],
    ):
        self.violations.append(
            action
        )

        result = {
            "flagged": True,
            "action": action,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
