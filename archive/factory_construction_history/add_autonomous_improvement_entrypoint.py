from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

marker = "\n    def history(self):"

if "def run_autonomous_improvement" in text:
    print({
        "status": "ALREADY_EXISTS"
    })
    raise SystemExit

method = '''
    def run_autonomous_improvement(self):
        metrics = {}

        if hasattr(self, "get_assessment_metrics"):
            metrics = self.get_assessment_metrics()

        elif hasattr(self, "improvement_assessment"):
            assessment = self.improvement_assessment.assess()
            metrics = {
                "assessment": assessment
            }

        result = self.improvement_orchestrator.run_cycle(
            metrics
        )

        return result

'''

if marker not in text:
    print({
        "status": "ERROR",
        "reason": "history marker not found"
    })
    raise SystemExit

text = text.replace(
    marker,
    "\n" + method + marker
)

p.write_text(text)

print({
    "status": "PATCHED",
    "target": "ai/factory/runtime.py",
    "next_action": "VERIFY_COMPILE"
})
