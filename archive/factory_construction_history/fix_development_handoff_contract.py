from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

start = text.find("            findings = []")

end = text.find(
    "            development_result = self.development_pipeline.run_development_cycle(",
    start
)

if start == -1 or end == -1:
    print({
        "status": "ERROR",
        "reason": "development handoff section not found"
    })
    raise SystemExit

call_end = text.find(
    "            )",
    end
)

replacement = """            findings = [
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
"""

text = text[:start] + replacement + text[call_end + len("            )"):]

p.write_text(text)

print({
    "status": "PATCHED",
    "next_action": "VERIFY_COMPILE"
})
