from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

old = '''                if hasattr(self, "improvement_audit"):
                    self.improvement_audit.record(
                        {
                            "type": "autonomous_improvement_execution",
                            "result": result,
                        }
                    )

                executed.append(result)
'''

new = '''                if hasattr(self, "improvement_audit"):
                    self.improvement_audit.record(
                        {
                            "type": "autonomous_improvement_execution",
                            "result": result,
                        }
                    )

                if (
                    isinstance(result, dict)
                    and result.get("status") == "EXECUTED"
                    and hasattr(self, "checkpoint_manager")
                ):
                    self.checkpoint_manager.create_checkpoint(
                        {
                            "type": "autonomous_improvement",
                            "improvement": approved,
                            "result": result,
                        }
                    )

                executed.append(result)
'''

if old in text:
    text = text.replace(old, new)

path.write_text(text)

print({
    "status": "AUTONOMOUS_CHECKPOINT_BRIDGE_INSTALLED"
})
