from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

old = '''            {
                "objective": objective,
                "proposal": development,
                "plan": plan,
                "source": "factory_proposal",
            }
'''

new = '''            {
                "objective": objective,
                "proposal": development,
                "plan": plan,
                "source": "factory_proposal",
                "capability_source": "capability_graph",
                "capability_context": findings.get(
                    "discovery",
                    {}
                ),
            }
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
