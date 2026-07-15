class IntelligenceDriftDetector:

    def compare(self, previous, current):

        drift = []

        if previous.get("confidence") != current.get("confidence"):
            drift.append(
                {
                    "type":
                    "confidence_change",
                    "previous":
                    previous.get("confidence"),
                    "current":
                    current.get("confidence"),
                }
            )

        if previous.get("situation") != current.get("situation"):
            drift.append(
                {
                    "type":
                    "situation_change",
                }
            )

        if previous.get("diagnosis") != current.get("diagnosis"):
            drift.append(
                {
                    "type":
                    "diagnosis_change",
                }
            )

        return {
            "drift_detected":
                len(drift) > 0,

            "changes":
                drift,

            "mode":
                "read_only",
        }
