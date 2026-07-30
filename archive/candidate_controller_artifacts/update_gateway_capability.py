from pathlib import Path

p = Path("ai/factory/authority_gateway.py")

text = p.read_text()

if "FactoryCapabilityGraphIntelligence" not in text:
    text = text.replace(
        "from ai.factory.development_pipeline import FactoryDevelopmentPipeline\n",
        "from ai.factory.development_pipeline import FactoryDevelopmentPipeline\nfrom ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence\n",
    )

old = '''    def submit_goal(self, objective):

        development_request = self.runtime.submit_development_request(
            objective,
            "authority_gateway_submission",
        )

        return {
            "development_request": development_request,
            "state": "ready_for_review"
        }
'''

new = '''    def submit_goal(self, objective):

        capability_graph = FactoryCapabilityGraphIntelligence(
            self.runtime
        ).analyze()

        development_request = self.runtime.submit_development_request(
            objective,
            "authority_gateway_submission",
        )

        return {
            "development_request": development_request,
            "capability_graph": capability_graph,
            "state": "ready_for_review"
        }
'''

if old not in text:
    raise SystemExit("TARGET_NOT_FOUND")

p.write_text(text.replace(old, new, 1))
print("UPDATED")
