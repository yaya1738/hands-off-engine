from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

imp = "from ai.factory.capability_gap_analyzer import FactoryCapabilityGapAnalyzer\n"

if "FactoryCapabilityEvolutionDecision" not in text:
    text = text.replace(
        imp,
        imp + "from ai.factory.capability_evolution_decision import FactoryCapabilityEvolutionDecision\n"
    )

old = "        self.capability_consolidation_loader = FactoryCapabilityConsolidationLoader()\n"

new = old + "        self.capability_evolution_decision = FactoryCapabilityEvolutionDecision()\n"

if "self.capability_evolution_decision" not in text:
    text = text.replace(old, new, 1)

p.write_text(text)

print("PATCH_APPLIED")
