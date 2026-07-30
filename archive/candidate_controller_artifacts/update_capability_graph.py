from pathlib import Path

p = Path("ai/factory/capability_graph_intelligence.py")

text = p.read_text()

old = '''    def infer_capability(self, name):

        mappings = {
'''

new = '''    def infer_capability(self, name):

        onboarded = self.runtime.capability_onboarding.list_capabilities()

        for capability in onboarded:
            if capability.get("name") == name:
                return capability.get(
                    "description",
                    "onboarded_capability",
                )

        registered = self.runtime.improvement_capability_registry.list_capabilities()

        if name in registered:
            return "registered_improvement_capability"

        mappings = {
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
