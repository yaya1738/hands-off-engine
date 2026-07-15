class CredentialDiagnosticResolver:

    def resolve(self, knowledge_matches):

        if not knowledge_matches:
            return {
                "primary":
                "insufficient_evidence",
                "confidence": 0.5,
                "mode": "read_only"
            }

        ranked = sorted(
            knowledge_matches,
            key=lambda x:
            x.get("confidence", 0),
            reverse=True
        )

        primary = ranked[0]

        secondary = ranked[1:]

        return {
            "primary_diagnosis":
                primary["diagnosis"],

            "confidence":
                primary["confidence"],

            "evidence_pattern":
                primary["pattern"],

            "secondary_observations":
                [
                    item["diagnosis"]
                    for item in secondary
                ],

            "mode":
                "read_only"
        }
