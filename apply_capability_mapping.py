from pathlib import Path

p = Path("ai/factory/capability_graph_intelligence.py")

text = p.read_text()

old = '''        mappings = {
            "goal": "objective_management",
'''

new = '''        mappings = {
            "capability": "capability_management",
            "onboarding": "capability_management",
            "development": "development_orchestration",
            "entry": "development_orchestration",
            "goal": "objective_management",
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
