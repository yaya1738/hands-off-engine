from pathlib import Path

path = Path("ai/factory/feedback_engine.py")
text = path.read_text()

# Ensure history storage exists
if "self._history" not in text:
    text = text.replace(
        "class FactoryFeedbackEngine:",
        "class FactoryFeedbackEngine:\n    def __init__(self, memory=None):\n        self.memory = memory\n        self._history = []\n"
    )

# Add analyze history append
text = text.replace(
'''        return {
            "patterns": patterns,
        }
''',
'''        result = {
            "patterns": patterns,
        }

        self._history.append(
            result
        )

        return result
'''
)

# Add score
if "def score(" not in text:
    text += '''

    def score(
        self,
        result,
    ):
        score = 1 if result.get(
            "success"
        ) else 0

        output = {
            "score": score,
        }

        self._history.append(
            output
        )

        return output


    def history(self):
        return self._history
'''

path.write_text(text)

print({
    "status": "FEEDBACK_ENGINE_CONTRACT_FIXED"
})
