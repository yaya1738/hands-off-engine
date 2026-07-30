from pathlib import Path

# Decision engine
path = Path("ai/factory/decision_engine.py")

if path.exists():
    text = path.read_text()

    if "def analyze(" not in text:
        marker = "    def decide("
        insert = """    def analyze(
        self,
        health,
        history,
        telemetry,
    ):
        return self.decide({
            "health": health,
            "history": history,
            "telemetry": telemetry,
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
        })

"""
        text = text.replace(marker, insert + marker)

    path.write_text(text)


# Factory decision logic
path = Path("ai/factory/decision_engine.py")

if path.exists():
    text = path.read_text()

    text = text.replace(
        '"decision": "CONTINUE"',
        '"decision": ("OPTIMIZE" if data.get("recommendation") == "improve" else "CONTINUE")'
    )

    if '"confidence"' not in text:
        text = text.replace(
            '"decision":',
            '"confidence": data.get("performance", 0),\n            "decision":',
            1
        )

    path.write_text(text)


print({
    "status": "DECISION_ENGINE_CONTRACT_FIXED"
})
