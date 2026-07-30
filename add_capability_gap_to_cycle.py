from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

old = """        improvement_cycle = self.improvement_orchestrator.run_cycle(
            {
                "success_rate": 1 if result.get("success") else 0,
                "average_impact": 0.5,
            }
        )
"""

new = """        capability_gap_analysis = self.capability_gap_analyzer.analyze()

        improvement_cycle = self.improvement_orchestrator.run_cycle(
            {
                "success_rate": 1 if result.get("success") else 0,
                "average_impact": 0.5,
                "capability_gap_analysis": capability_gap_analysis,
            }
        )
"""

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

text = text.replace(old, new, 1)

p.write_text(text)

print("PATCH_APPLIED")
