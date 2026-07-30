from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = """        capability_consolidation = (
            self.capability_consolidation_loader.load()
        )
"""

new = old + """
        capability_evolution_decision = (
            self.capability_evolution_decision.decide(
                capability_gap_analysis,
                capability_consolidation,
            )
        )
"""

if "capability_evolution_decision = (" not in text:
    if old not in text:
        raise SystemExit("INSERT_POINT_NOT_FOUND")
    text = text.replace(old, new, 1)

old_return = """            "capability_consolidation": capability_consolidation,
            "decision": decision_selection,
"""

new_return = """            "capability_consolidation": capability_consolidation,
            "capability_evolution_decision": capability_evolution_decision,
            "decision": decision_selection,
"""

if '"capability_evolution_decision": capability_evolution_decision' not in text:
    if old_return not in text:
        raise SystemExit("RETURN_POINT_NOT_FOUND")
    text = text.replace(old_return, new_return, 1)

old_audit = """                "decision": decision_selection,
                "development": development_result,
"""

new_audit = """                "decision": decision_selection,
                "capability_evolution_decision": capability_evolution_decision,
                "development": development_result,
"""

if '"capability_evolution_decision": capability_evolution_decision' not in text:
    if old_audit not in text:
        raise SystemExit("AUDIT_POINT_NOT_FOUND")
    text = text.replace(old_audit, new_audit, 1)

p.write_text(text)

print("PATCH_APPLIED")
