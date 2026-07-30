from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

if "FactoryCapabilityGapAnalyzer" not in text:
    text = text.replace(
        "from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence\n",
        "from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence\nfrom ai.factory.capability_gap_analyzer import FactoryCapabilityGapAnalyzer\n",
        1,
    )

old = """        self.artifact_registry = FactoryArtifactRegistry()
        self.capability_onboarding = FactoryCapabilityOnboarding()
        self.improvement_capability_registry = FactoryImprovementCapabilityRegistry()
        self.change_validation = FactoryChangeValidation()
"""

new = """        self.artifact_registry = FactoryArtifactRegistry()
        self.capability_onboarding = FactoryCapabilityOnboarding()
        self.improvement_capability_registry = FactoryImprovementCapabilityRegistry()
        self.capability_graph_intelligence = FactoryCapabilityGraphIntelligence(self)
        self.capability_gap_analyzer = FactoryCapabilityGapAnalyzer(self)
        self.change_validation = FactoryChangeValidation()
"""

if "self.capability_gap_analyzer" not in text:
    if old not in text:
        raise SystemExit("INIT_TARGET_NOT_FOUND")
    text = text.replace(old, new, 1)

text = text.replace(
"""            capability_graph = FactoryCapabilityGraphIntelligence(
                self
            ).analyze()
""",
"""            capability_graph = self.capability_graph_intelligence.analyze()
"""
)

p.write_text(text)

print("PATCH_APPLIED")
