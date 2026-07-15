from typing import Dict, Any


class FactoryVerifier:
    def verify(self, execution: Any) -> Dict[str, Any]:
        issues = []

        if execution.status != "SUCCESS":
            issues.append("execution_failed")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
        }
