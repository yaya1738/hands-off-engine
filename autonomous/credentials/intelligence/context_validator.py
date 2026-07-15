class ContextValidator:

    REQUIRED = [
        "context",
        "situation",
        "diagnosis",
        "confidence",
        "safety",
        "mode",
    ]

    def validate(self, data):

        missing = [
            key
            for key in self.REQUIRED
            if key not in data
        ]

        confidence = data.get(
            "confidence",
            -1
        )

        safety = data.get(
            "safety",
            {}
        )

        valid_confidence = (
            0 <= confidence <= 1
        )

        safety_verified = (
            safety.get(
                "actions_allowed"
            ) is False
        )

        return {
            "valid":
                len(missing) == 0
                and valid_confidence
                and safety_verified,

            "missing_fields":
                missing,

            "safety_verified":
                safety_verified,

            "mode":
                "read_only",
        }
