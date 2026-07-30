from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

marker = """        return {
            "cycle": cycle_result,
            "development": development_result,
            "execution": execution_result,
            "diagnostics": diagnostics
        }
"""

replacement = """        return {
            "cycle": cycle_result,
            "development": development_result,
            "execution": execution_result,
            "diagnostics": diagnostics
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
"""

if marker not in text:
    print({
        "status": "ERROR",
        "reason": "return marker not found"
    })
    raise SystemExit

text = text.replace(marker, replacement)

p.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "COMPILE"
})
