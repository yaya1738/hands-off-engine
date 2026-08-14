from datetime import datetime, timezone


class FactoryAutonomyManager:

    def __init__(self, runtime):
        self.runtime = runtime
        self._authority_gateway = None

    def _authority(self):
        if self._authority_gateway is None:
            from ai.factory.authority_gateway import FactoryAuthorityGateway
            self._authority_gateway = FactoryAuthorityGateway(runtime=self.runtime)
        return self._authority_gateway

    def evaluate(self, objective):
        components = self.runtime.component_inventory()
        capability_count = components.get("component_count", 0)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "objective": objective,
            "factory_components": capability_count,
            "status": "ready" if capability_count > 0 else "blocked",
        }

    def execute(self, objective):
        evaluation = self.evaluate(objective)
        if evaluation["status"] != "ready":
            return {"evaluation": evaluation, "status": "blocked"}

        result = self._authority().execute_autonomous(objective)
        return {"evaluation": evaluation, "execution": result}

    def system_analysis(self):
        from ai.factory.system_intelligence import FactorySystemIntelligence
        return FactorySystemIntelligence(self.runtime).analyze()

    def consolidation_analysis(self):
        from ai.factory.consolidation_intelligence import FactoryConsolidationIntelligence
        return FactoryConsolidationIntelligence(self.runtime).analyze()

    def capability_graph_analysis(self):
        from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence
        return FactoryCapabilityGraphIntelligence(self.runtime).analyze()

    def role_analysis(self):
        from ai.factory.role_analysis_intelligence import FactoryRoleAnalysisIntelligence
        return FactoryRoleAnalysisIntelligence(self.runtime).analyze()

    def usage_analysis(self):
        from ai.factory.usage_intelligence import FactoryUsageIntelligence
        return FactoryUsageIntelligence(self.runtime).analyze()

    def consolidation_decision_analysis(self):
        from ai.factory.consolidation_decision_engine import FactoryConsolidationDecisionEngine
        return FactoryConsolidationDecisionEngine(self.runtime).analyze()

    def discovery_gate(self, objective, context=""):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "objective": objective,
            "context": context,
            "component_inventory": self.runtime.component_inventory(),
            "system_analysis": self.system_analysis(),
            "capability_graph_analysis": self.capability_graph_analysis(),
            "role_analysis": self.role_analysis(),
            "usage_analysis": self.usage_analysis(),
            "consolidation_analysis": self.consolidation_analysis(),
            "consolidation_decision_analysis": self.consolidation_decision_analysis(),
        }
