from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

imp = "from ai.factory.capability_gap_analyzer import FactoryCapabilityGapAnalyzer\n"

if "capability_consolidation_loader" not in text:
    text = text.replace(
        imp,
        imp + "from ai.factory.capability_consolidation_loader import FactoryCapabilityConsolidationLoader\n"
    )

old = "        self.capability_gap_analyzer = FactoryCapabilityGapAnalyzer(self)\n"

new = old + "        self.capability_consolidation_loader = FactoryCapabilityConsolidationLoader()\n"

if "self.capability_consolidation_loader" not in text:
    text = text.replace(old, new, 1)

p.write_text(text)

print("PATCH_APPLIED")
