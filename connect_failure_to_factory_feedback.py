from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = '''            diagnostics = None

            if hasattr(self, "diagnostic_intelligence"):
                diagnostics = self.diagnostic_intelligence.analyze(
                    [failure]
                )

            return {
                "status": "AUTONOMOUS_IMPROVEMENT_FAILED",
                "failure": failure,
                "diagnostics": diagnostics
            }
'''

new = '''            diagnostics = None
            feedback_goal = None

            if hasattr(self, "diagnostic_intelligence"):
                diagnostics = self.diagnostic_intelligence.analyze(
                    [failure]
                )

            if hasattr(self, "submit_goal"):
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

if old not in text:
    print({
        "status": "ERROR",
        "reason": "exception handler block not found"
    })
    raise SystemExit

text = text.replace(old, new)

p.write_text(text)

print({
    "status": "PATCHED"
})
