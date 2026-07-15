class CredentialMetrics:

    def calculate(self, events):

        return {
            "total_events": len(events),
            "recovery_events": len(
                [
                    e for e in events
                    if "RECOVERY" in str(e.get("to"))
                ]
            ),
            "authorization_events": len(
                [
                    e for e in events
                    if "AUTH" in str(e.get("to"))
                ]
            ),
        }
