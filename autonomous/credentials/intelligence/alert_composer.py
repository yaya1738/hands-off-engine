class AlertComposer:

    def compose(self, regression):

        if regression.get(
            "regression_detected"
        ):
            return {
                "alert_level": "warning",
                "type": regression.get(
                    "reason"
                ),
                "message":
                    "Intelligence confidence regression detected",
                "evidence": {
                    "previous":
                    regression.get(
                        "previous_confidence"
                    ),
                    "current":
                    regression.get(
                        "current_confidence"
                    ),
                },
                "mode": "read_only",
            }

        return {
            "alert_level": "normal",
            "type": "none",
            "message":
                "No intelligence regression detected",
            "mode": "read_only",
        }
