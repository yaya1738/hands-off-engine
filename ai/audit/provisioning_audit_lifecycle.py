from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class LifecycleResult:
    valid: bool
    schema_version: str
    retention_class: str
    issues: List[str]


class ProvisioningAuditLifecycle:
    def annotate(
        self,
        record: Any,
        schema_version: str,
        retention_class: str,
    ) -> Dict[str, Any]:
        return {
            "record": record,
            "schema_version": schema_version,
            "retention_class": retention_class,
        }

    def validate_schema(
        self,
        event: Dict[str, Any],
    ) -> LifecycleResult:
        issues = []

        if not event.get("schema_version"):
            issues.append("missing_schema_version")

        if not event.get("retention_class"):
            issues.append("missing_retention_class")

        return LifecycleResult(
            valid=len(issues) == 0,
            schema_version=event.get("schema_version", ""),
            retention_class=event.get("retention_class", ""),
            issues=issues,
        )
