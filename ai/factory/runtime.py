from typing import Any, Dict, List

from ai.factory.runtime_governance import FactoryRuntimeGovernance
from ai.factory.planning_intelligence import FactoryPlanningIntelligence
from ai.factory.simulation_intelligence import FactorySimulationIntelligence
from ai.factory.decision_intelligence import FactoryDecisionIntelligence
from ai.factory.orchestration_intelligence import FactoryOrchestrationIntelligence
from ai.factory.execution_intelligence import FactoryExecutionIntelligence
from ai.factory.learning_intelligence import FactoryLearningIntelligence
from ai.factory.optimization_intelligence import FactoryOptimizationIntelligence


class FactoryRuntime:
    def __init__(self):
        self.governance = FactoryRuntimeGovernance()

        self.planning = FactoryPlanningIntelligence()
        self.simulation = FactorySimulationIntelligence()
        self.decision = FactoryDecisionIntelligence()
        self.orchestration = FactoryOrchestrationIntelligence()
        self.execution = FactoryExecutionIntelligence()
        self.learning = FactoryLearningIntelligence()
        self.optimization = FactoryOptimizationIntelligence()

        self._history: List[Dict[str, Any]] = []

    def execute(
        self,
        goal: Dict[str, Any],
    ):
        steps = []

        self.governance.check_policy(goal)
        steps.append("policy_check")

        self.governance.check_permission(goal)
        steps.append("permission_check")

        self.governance.assess_risk(goal)
        steps.append("risk_check")

        self.governance.authorize_execution(goal)
        steps.append("authorization")

        plan = self.planning.create_plan(goal)
        steps.append("planning")

        simulation = self.simulation.run_simulation(plan)
        steps.append("simulation")

        decision = self.decision.create_decision(simulation)
        steps.append("decision")

        self.orchestration.dispatch_tasks(
            [decision]
        )
        steps.append("orchestration")

        self.execution.create_execution(
            "runtime-job",
            decision,
        )
        self.execution.start_execution(
            "runtime-job"
        )
        self.execution.complete_execution(
            "runtime-job"
        )
        steps.append("execution")

        self.governance.audit_execution(
            {
                "goal": goal,
                "steps": steps,
            }
        )
        steps.append("audit")

        self.learning.record_experience(
            {
                "goal": goal,
                "steps": steps,
            }
        )
        steps.append("learning")

        self.optimization.measure_performance(
            {
                "steps": len(steps),
            }
        )
        steps.append("optimization")

        result = {
            "success": True,
            "goal": goal,
            "steps_completed": steps,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
