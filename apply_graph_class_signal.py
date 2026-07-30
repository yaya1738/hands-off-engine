from pathlib import Path

p = Path("ai/factory/capability_graph_intelligence.py")

text = p.read_text()

old = '''            graph[component] = {
                "provides": self.infer_capability(component),
                "status": "active",
                "redundancy": 0,
            }
'''

new = '''            graph[component] = {
                "provides": self.infer_capability(
                    component + "_" + str(
                        type(getattr(self.runtime, component)).__name__
                    )
                ),
                "status": "active",
                "redundancy": 0,
            }
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
