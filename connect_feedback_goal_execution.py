from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = '''            if hasattr(self, "submit_goal"):
                feedback_goal = self.submit_goal({
                    "type": "capability_gap",
                    "target": "AUTONOMOUS_FAILURE_REPAIR",
                    "reason": str(e)
                })

            return {
                "status": "AUTONOMOUS_IMPROVEMENT_FAILED",
                "failure": failure,
                "diagnostics": diagnostics,
                "feedback_goal": feedback_goal
            }
'''

new = '''            if hasattr(self, "submit_goal"):
                repair_objective = {
                    "type": "capability_gap",
                    "target": "AUTONOMOUS_FAILURE_REPAIR",
                    "reason": str(e)
                }

                feedback_goal = self.submit_goal(
                    repair_objective
                )

            repair_execution = None

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

if old not in text:
    print({
        "status": "ERROR",
        "reason": "feedback goal block not found"
    })
    raise SystemExit

text = text.replace(old, new)
p.write_text(text)

print({
    "status": "PATCHED"
})
