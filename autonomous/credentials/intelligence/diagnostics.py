class CredentialDiagnosticEngine:

    def diagnose(self, metrics=None, trends=None, temporal=None):

        metrics = metrics or {}
        trends = trends or {}
        temporal = temporal or {}

        findings = []

        reasons = trends.get(
            "reason_counts",
            {}
        )

        if reasons.get(
            "adapter_requires_external_consent",
            0
        ):

            findings.append(
                {
                    "cause":
                    "authorization_consent_required",
                    "confidence":
                    0.85
                }
            )

        if temporal.get(
            "event_count",
            0
        ) > 10:

            findings.append(
                {
                    "cause":
                    "high_event_frequency",
                    "confidence":
                    0.75
                }
            )

        if not findings:

            findings.append(
                {
                    "cause":
                    "no_anomaly_detected",
                    "confidence":
                    0.90
                }
            )

        return {
            "diagnostics": findings,
            "mode": "read_only"
        }
