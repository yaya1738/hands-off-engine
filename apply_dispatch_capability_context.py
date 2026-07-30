from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

old = '''            self.orchestration.dispatch_tasks(
                [decision]
            )
'''

new = '''            capability_graph = FactoryCapabilityGraphIntelligence(
                self
            ).analyze()

            decision["capability_context"] = capability_graph.get(
                "capability_graph",
                {}
            )

            self.orchestration.dispatch_tasks(
                [decision]
            )
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
