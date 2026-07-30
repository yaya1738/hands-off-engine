from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

old = """        capability_gap_analysis = self.capability_gap_analyzer.analyze()

        improvement_cycle = self.improvement_orchestrator.run_cycle(
"""

new = """        capability_gap_analysis = self.capability_gap_analyzer.analyze()

        capability_consolidation = (
            self.capability_consolidation_loader.load()
        )

        improvement_cycle = self.improvement_orchestrator.run_cycle(
"""

if old not in text:
    raise SystemExit("FIRST_TARGET_NOT_FOUND")

text = text.replace(old, new, 1)

old2 = '"capability_gap_analysis": capability_gap_analysis,\n'

new2 = '"capability_gap_analysis": capability_gap_analysis,\n                "capability_consolidation": capability_consolidation,\n'

if old2 not in text:
    raise SystemExit("SECOND_TARGET_NOT_FOUND")

text = text.replace(old2, new2, 1)

old3 = '"capability_gap_analysis": capability_gap_analysis,\n            "decision": decision_selection,'

new3 = '"capability_gap_analysis": capability_gap_analysis,\n            "capability_consolidation": capability_consolidation,\n            "decision": decision_selection,'

if old3 not in text:
    raise SystemExit("THIRD_TARGET_NOT_FOUND")

text = text.replace(old3, new3, 1)

p.write_text(text)

print("PATCH_APPLIED")
