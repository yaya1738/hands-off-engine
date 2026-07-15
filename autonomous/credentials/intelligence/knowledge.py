class CredentialKnowledgeBase:

    def __init__(self):

        self.patterns = {

            "authorization_consent_loop": {
                "signals": [
                    "adapter_requires_external_consent",
                    "REQUESTED->AWAITING_AUTHORIZATION"
                ],
                "diagnosis":
                    "authorization_consent_required",
                "confidence":
                    0.85
            },

            "provider_failure": {
                "signals": [
                    "provider_unavailable"
                ],
                "diagnosis":
                    "provider_connectivity_issue",
                "confidence":
                    0.75
            },

            "normal_operation": {
                "signals": [],
                "diagnosis":
                    "no_known_anomaly",
                "confidence":
                    0.90
            }
        }


    def analyze(self, signals):

        matches = []

        for name, pattern in self.patterns.items():

            required = pattern["signals"]

            if all(
                signal in signals
                for signal in required
            ):

                matches.append(
                    {
                        "pattern": name,
                        "diagnosis":
                            pattern["diagnosis"],
                        "confidence":
                            pattern["confidence"]
                    }
                )

        if not matches:

            matches.append(
                {
                    "pattern":
                    "unknown",
                    "diagnosis":
                    "insufficient_evidence",
                    "confidence":
                    0.50
                }
            )

        return {
            "knowledge_matches": matches,
            "mode": "read_only"
        }
