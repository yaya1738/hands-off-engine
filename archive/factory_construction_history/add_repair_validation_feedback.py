from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = '''            repair_execution = None

            if feedback_goal and hasattr(self, "execute"):
                repair_execution = self.execute(
                    repair_objective
                )

            return {
                "status": "AUTONOMOUS_IMPROVEMENT_FAILED",
                "failure": failure,
                "diagnostics": diagnostics,
                "feedback_goal": feedback_goal,
                "repair_execution": repair_execution
            }
'''

new = '''            repair_execution = None
            validation_result = None

            if feedback_goal and hasattr(self, "execute"):
                repair_execution = self.execute(
                    repair_objective
                )

            if hasattr(self, "improvement_assessment"):
                validation_result = self.improvement_assessment.assess()

            return {
                "status": "AUTONOMOUS_IMPROVEMENT_FAILED",
                "failure": failure,
                "diagnostics": diagnostics,
                "feedback_goal": feedback_goal,
                "repair_execution": repair_execution,
                "validation": validation_result
            }
'''

if old not in text:
    print({
        "status": "ERROR",
        "reason": "repair block not found"
    })
    raise SystemExit

text = text.replace(old, new)
p.write_text(text)

print({
    "status": "PATCHED"
})
