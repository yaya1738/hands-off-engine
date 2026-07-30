from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = """        return {
            "cycle": cycle_result,
            "development": development_result,
            "execution": execution_result
        }
"""

new = """        diagnostics = None

        failures = []

        if isinstance(development_result, dict):
            if development_result.get("status") == "FAILED":
                failures.append(development_result)

        if isinstance(execution_result, dict):
            for item in execution_result.get("executed", []):
                if item.get("status") in ("FAILED", "BLOCKED"):
                    failures.append(item)

        if failures and hasattr(self, "diagnostic_intelligence"):
            diagnostics = self.diagnostic_intelligence.analyze(
                failures
            )

        return {
            "cycle": cycle_result,
            "development": development_result,
            "execution": execution_result,
            "diagnostics": diagnostics
        }
"""

if old not in text:
    print({
        "status": "ERROR",
        "reason": "return block not found"
    })
    raise SystemExit

text = text.replace(old, new)
p.write_text(text)

print({
    "status": "PATCHED"
})
