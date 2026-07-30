from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

start = text.find("    def run_autonomous_improvement(self):")
end = text.find("\n    def ", start + 10)

if start == -1 or end == -1:
    print({"status": "ERROR", "reason": "method boundaries not found"})
    raise SystemExit

new_method = '''    def run_autonomous_improvement(self):
        try:
            metrics = {}

            if hasattr(self, "get_assessment_metrics"):
                metrics = self.get_assessment_metrics()
            elif hasattr(self, "improvement_assessment"):
                assessment = self.improvement_assessment.assess()
                metrics = {
                    "assessment": assessment
                }

            cycle_result = self.improvement_orchestrator.run_cycle(
                metrics
            )

            development_result = None

            if hasattr(self, "development_pipeline"):
                plan = cycle_result.get("plan", {})
                findings = [
                    {
                        "objective": task,
                        "source": "autonomous_improvement",
                        "priority": plan.get("priority", 1)
                    }
                    for task in plan.get("tasks", [])
                ]

                development_result = self.development_pipeline.run_development_cycle(
                    findings
                )

            execution_result = self.execute_autonomous_improvements(
                cycle_result
            )

            return {
                "cycle": cycle_result,
                "development": development_result,
                "execution": execution_result
            }

        except Exception as e:
            failure = {
                "status": "FAILED",
                "component": "run_autonomous_improvement",
                "error": str(e)
            }

            diagnostics = None

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

text = text[:start] + new_method + text[end:]

p.write_text(text)

print({"status": "REPLACED"})
