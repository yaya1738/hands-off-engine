from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

old = '''            if hasattr(self, "improvement_action_resolver"):
                action = self.improvement_action_resolver.resolve(
                    approved
                )
'''

new = '''            if hasattr(self, "improvement_action_resolver"):
                resolver_input = {
                    "action": approved.get(
                        "name",
                        "generic_improvement"
                    )
                    if isinstance(approved, dict)
                    else "generic_improvement"
                }

                action = self.improvement_action_resolver.resolve(
                    resolver_input
                )

'''

if old in text:
    text = text.replace(old, new)

path.write_text(text)

print({
    "status": "QUEUE_TO_RESOLVER_ADAPTER_INSTALLED"
})
