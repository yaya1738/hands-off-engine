from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = '''            development_result = None

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
'''

new = '''            execution_result = self.execute_autonomous_improvements(
                cycle_result
            )

            return {
                "cycle": cycle_result,
                "development": None,
                "execution": execution_result
            }
'''

if old not in text:
    print({
        "status": "FAILED",
        "reason": "autonomous_development_block_not_found"
    })
else:
    path.write_text(text.replace(old, new))
    print({
        "status": "PATCHED",
        "target": "remove_development_bypass",
        "next_action": "VERIFY_COMPILE"
    })
