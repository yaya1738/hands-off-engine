import hashlib
import json
from typing import Any, Dict


class ProvisioningAuditSnapshot:
    def create(
        self,
        records: Any,
        evidence: Dict[str, Any],
        summary: Dict[str, Any],
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = {
            "records": records,
            "evidence": evidence,
            "summary": summary,
            "report": report,
        }

        snapshot_hash = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()

        return {
            "snapshot_id": snapshot_hash,
            **payload,
        }
