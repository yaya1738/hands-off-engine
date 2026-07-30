from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = """        self.improvement_audit.record(
            {
                "type": "runtime_improvement_cycle",
                "proposal": improvement_cycle,
                "decision": decision_selection,
                "development": development_result,
                "plan": development_plan,
                "task": development_task,
            }
        )
"""

new = old + """
        return {
            "improvement_cycle": improvement_cycle,
            "capability_gap_analysis": capability_gap_analysis,
            "decision": decision_selection,
            "development": development_result,
            "plan": development_plan,
            "task": development_task,
        }
"""

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))

print("PATCH_APPLIED")
