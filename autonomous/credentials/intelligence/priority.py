class CredentialPriorityResolver:

    PRIORITY = {
        "authorization_consent_required": 90,
        "provider_connectivity_issue": 80,
        "state_conflict": 85,
        "no_known_anomaly": 10,
    }


    def resolve(self, diagnoses):

        ranked = sorted(
            diagnoses,
            key=lambda x:
            (
                self.PRIORITY.get(
                    x.get("diagnosis"),
                    0
                ),
                x.get("confidence", 0)
            ),
            reverse=True
        )

        if not ranked:
            return {
                "diagnosis":
                "insufficient_evidence",
                "mode":
                "read_only"
            }

        primary = ranked[0]

        return {
            "primary_diagnosis":
                primary["diagnosis"],

            "priority":
                self.PRIORITY.get(
                    primary["diagnosis"],
                    0
                ),

            "confidence":
                primary.get(
                    "confidence",
                    0
                ),

            "mode":
                "read_only"
        }
