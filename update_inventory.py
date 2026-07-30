from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

old = '''        return {
            "component_count": len(
                self.registry.list_components()
            ),
            "components": self.registry.list_components(),
        }
'''

new = '''        return {
            "component_count": len(
                self.registry.list_components()
            ),
            "components": self.registry.list_components(),
            "capabilities": {
                "onboarded": self.capability_onboarding.list_capabilities(),
                "registered": self.improvement_capability_registry.list_capabilities(),
            },
        }
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
