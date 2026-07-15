class DecisionContextBuilder:

    def build(
        self,
        situation,
        diagnosis,
        confidence,
        evidence,
        history,
        safety,
    ):

        return {
            "context":
                "credential_bridge",

            "situation":
                situation,

            "diagnosis":
                diagnosis,

            "confidence":
                confidence,

            "evidence":
                evidence,

            "history":
                history,

            "safety":
                safety,

            "mode":
                "read_only",
        }
