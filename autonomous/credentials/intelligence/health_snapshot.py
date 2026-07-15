class IntelligenceHealthSnapshot:

    def build(
        self,
        health,
        stability,
        confidence,
        drift,
        situation,
        safety,
    ):

        return {
            "system":
                "credential_bridge",

            "health":
                health,

            "stability":
                stability,

            "confidence":
                confidence,

            "drift":
                drift,

            "situation":
                situation,

            "safety":
                safety,

            "mode":
                "read_only",
        }
