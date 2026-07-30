from pathlib import Path

path = Path("ai/factory/decision_engine.py")
text = path.read_text()

# Add missing methods before class end / before reason if present
if "def decide(" not in text:
    marker = "    def reason("

    methods = '''    def decide(
        self,
        state: Dict[str, Any],
    ):
        decision = self.evaluate(
            state
        )

        result = {
            "confidence": state.get(
                "performance",
                0,
            ),
            "decision": decision,
            "reason": self.reason(
                decision
            ),
        }

        if not hasattr(self, "_history"):
            self._history = []

        self._history.append(
            result
        )

        return result


    def analyze(
        self,
        health,
        history,
        telemetry,
    ):
        return self.decide(
            {
                "recommendation": (
                    "improve"
                    if health.get("status") == "FAILED"
                    else "continue"
                ),
                "performance": (
                    0
                    if health.get("status") == "FAILED"
                    else 1
                ),
                "telemetry": telemetry,
            }
        )


    def history(self):
        return getattr(
            self,
            "_history",
            [],
        )


'''

    text = text.replace(
        marker,
        methods + marker
    )

# Ensure imports
if "Dict" not in text.splitlines()[0:10].__str__():
    pass

path.write_text(text)

print({
    "status": "DECISION_ENGINE_API_RESTORED"
})
