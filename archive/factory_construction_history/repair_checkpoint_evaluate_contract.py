from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

text = text.replace(
'''                    checkpoint_plan = self.checkpoint_manager.evaluate(
                        checkpoint_request
                    )
''',
'''                    checkpoint_plan = self.checkpoint_manager.evaluate()
'''
)

path.write_text(text)

print({
    "status": "CHECKPOINT_EVALUATE_CONTRACT_FIXED"
})
