from typing import Any, Dict, List


class ProvisioningAnomalyDetector:
    def detect(self, records: List[Any]) -> Dict[str, Any]:
        anomalies = []

        denial_counts = {}

        for record in records:
            requester = getattr(record, "requester_identity", None)
            decision = getattr(record, "decision", None)

            if decision == "DENY":
                denial_counts[requester] = denial_counts.get(requester, 0) + 1

        for requester, count in denial_counts.items():
            if count > 1:
                anomalies.append(
                    {
                        "type": "repeated_denials",
                        "evidence": {
                            "requester_identity": requester,
                            "count": count,
                        },
                    }
                )

        return {
            "anomalies_detected": len(anomalies) > 0,
            "anomalies": anomalies,
        }
