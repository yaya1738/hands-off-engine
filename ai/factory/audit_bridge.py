from datetime import datetime, timezone
from typing import Any, Dict


class FactoryAuditBridge:
    def create_audit_event(
        self,
        task_id: str,
        action: str,
        result: Any,
    ) -> Dict[str, Any]:
        return {
            "source": "factory",
            "task_id": task_id,
            "action": action,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
