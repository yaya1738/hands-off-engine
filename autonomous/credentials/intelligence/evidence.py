class CredentialEvidenceAnalyzer:

    def analyze(self, diagnosis, signals=None):

        signals = signals or []

        supporting = []
        missing = []

        if diagnosis == "authorization_consent_required":

            if "adapter_requires_external_consent" in signals:
                supporting.append(
                    "external_consent_requested"
                )
            else:
                missing.append(
                    "external_consent_signal"
                )

            if "REQUESTED->AWAITING_AUTHORIZATION" in signals:
                supporting.append(
                    "authorization_state_reached"
                )
            else:
                missing.append(
                    "authorization_transition"
                )

            missing.append(
                "authorization_completion_confirmation"
            )

        else:

            supporting.append(
                "insufficient_anomaly_evidence"
            )


        confidence = min(
            1.0,
            len(supporting) /
            (
                len(supporting)
                +
                len(missing)
            )
            if (
                len(supporting)
                +
                len(missing)
            )
            else 1.0
        )

        return {
            "diagnosis": diagnosis,
            "supporting_evidence": supporting,
            "missing_evidence": missing,
            "confidence": confidence,
            "mode": "read_only"
        }
