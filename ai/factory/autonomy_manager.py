from datetime import datetime, timezone


class FactoryAutonomyManager:

    def __init__(self, runtime):
        self.runtime = runtime

    def evaluate(self, objective):

        components = (
            self.runtime.component_inventory()
        )

        capability_count = components.get(
            "component_count",
            0
        )

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "objective":
                objective,

            "factory_components":
                capability_count,

            "status":
                "ready" if capability_count > 0 else "blocked",
        }


    def execute(self, objective):

        evaluation = self.evaluate(
            objective
        )

        if evaluation["status"] != "ready":
            return {
                "evaluation": evaluation,
                "status": "blocked",
            }

        result = self.runtime.autonomous_execute(
            objective
        )

        return {
            "evaluation": evaluation,
            "execution": result,
        }


    def system_analysis(self):

        from ai.factory.system_intelligence import (
            FactorySystemIntelligence
        )

        intelligence = FactorySystemIntelligence(
            self.runtime
        )

        return intelligence.analyze()


    def consolidation_analysis(self):

        from ai.factory.consolidation_intelligence import (
            FactoryConsolidationIntelligence
        )

        intelligence = FactoryConsolidationIntelligence(
            self.runtime
        )

        return intelligence.analyze()


    def capability_graph_analysis(self):

        from ai.factory.capability_graph_intelligence import (
            FactoryCapabilityGraphIntelligence
        )

        intelligence = FactoryCapabilityGraphIntelligence(
            self.runtime
        )

        return intelligence.analyze()


    def role_analysis(self):

        from ai.factory.role_analysis_intelligence import (
            FactoryRoleAnalysisIntelligence
        )

        intelligence = FactoryRoleAnalysisIntelligence(
            self.runtime
        )

        return intelligence.analyze()


    def usage_analysis(self):

        from ai.factory.usage_intelligence import (
            FactoryUsageIntelligence
        )

        intelligence = FactoryUsageIntelligence(
            self.runtime
        )

        return intelligence.analyze()


    def consolidation_decision_analysis(self):

        from ai.factory.consolidation_decision_engine import (
            FactoryConsolidationDecisionEngine
        )

        engine = FactoryConsolidationDecisionEngine(
            self.runtime
        )

        return engine.analyze()


    def discovery_gate(self, objective, context=""):

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "objective":
                objective,

            "context":
                context,

            "component_inventory":
                self.runtime.component_inventory(),

            "system_analysis":
                self.system_analysis(),

            "capability_graph_analysis":
                self.capability_graph_analysis(),

            "role_analysis":
                self.role_analysis(),

            "usage_analysis":
                self.usage_analysis(),

            "consolidation_analysis":
                self.consolidation_analysis(),

            "consolidation_decision_analysis":
                self.consolidation_decision_analysis(),

        }
