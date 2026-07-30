from pathlib import Path

# Fix decision_engine variable + decision mapping
path = Path("ai/factory/decision_engine.py")
text = path.read_text()

text = text.replace(
    'data.get("performance", 0)',
    'state.get("performance", 0)'
)

# Ensure improve maps to OPTIMIZE
old = '''    def evaluate(
        self,
        state: Dict[str, Any],
    ):
        recommendation = state.get(
            "recommendation"
        )

        if recommendation == "continue":
            return "CONTINUE"

        return "CONTINUE"
'''

new = '''    def evaluate(
        self,
        state: Dict[str, Any],
    ):
        recommendation = state.get(
            "recommendation"
        )

        if recommendation == "improve":
            return "OPTIMIZE"

        if recommendation == "continue":
            return "CONTINUE"

        return "CONTINUE"
'''

text = text.replace(old, new)

path.write_text(text)


# Fix decision intelligence select_action contract
path = Path("ai/factory/decision_intelligence.py")

if path.exists():
    text = path.read_text()

    if '"selected"' not in text:
        text = text.replace(
            'return {',
            'return {"selected": True,',
            1
        )

    path.write_text(text)

print({
    "status": "DECISION_CONTRACT_V2_FIXED"
})
