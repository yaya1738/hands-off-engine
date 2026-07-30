from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

old = '''                result = self.improvement_executor.execute(
                    approved,
                    action
                )
                executed.append(result)
'''

new = '''                result = self.improvement_executor.execute(
                    approved,
                    action
                )

                if hasattr(self, "improvement_audit"):
                    self.improvement_audit.record(
                        {
                            "type": "autonomous_improvement_execution",
                            "result": result,
                        }
                    )

                executed.append(result)
'''

if old in text:
    text = text.replace(old, new)

path.write_text(text)

print({
    "status": "IMPROVEMENT_RECORDING_BRIDGE_INSTALLED"
})
