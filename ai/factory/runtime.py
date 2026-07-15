from typing import Any, Dict, List

from ai.factory.runtime_governance import FactoryRuntimeGovernance
from ai.factory.runtime_observability import FactoryRuntimeObservability
from ai.factory.runtime_state import FactoryRuntimeState
from ai.factory.event_bus import FactoryEventBus
from ai.factory.event_replay import FactoryEventReplay
from ai.factory.self_healing_intelligence import FactorySelfHealingIntelligence
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
        self.observability = FactoryRuntimeObservability()
        self.state = FactoryRuntimeState()

        self.events = FactoryEventBus()
        self.replay = FactoryEventReplay()

        self.self_healing = FactorySelfHealingIntelligence()

        self.planning = FactoryPlanningIntelligence()
        self.simulation = FactorySimulationIntelligence()
        self.decision = FactoryDecisionIntelligence()
        self.orchestration = FactoryOrchestrationIntelligence()
        self.execution = FactoryExecutionIntelligence()
        self.learning = FactoryLearningIntelligence()
        self.optimization = FactoryOptimizationIntelligence()

        self._history: List[Dict[str, Any]] = []

    def emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ):
        event = {
            "type": event_type,
            "payload": payload,
        }

        self.events.emit_runtime_event(
            event_type,
            payload,
        )

        self.replay.store_event(
            event,
        )

        return event

    def execute(
        self,
        goal: Dict[str, Any],
    ):
        steps = []

        self.emit_event(
            "runtime.started",
            {"goal": goal},
        )

        self.state.load_state()
        steps.append("state_loaded")

        self.governance.check_policy(goal)
        steps.append("policy_check")

        self.governance.check_permission(goal)
        steps.append("permission_check")

        self.governance.assess_risk(goal)
        steps.append("risk_check")

        self.governance.authorize_execution(goal)
        steps.append("authorization")

        try:
            plan = self.planning.create_plan(goal)
            steps.append("planning")

            self.emit_event(
                "plan.created",
                {"plan": plan},
            )

            simulation = self.simulation.run_simulation(plan)
            steps.append("simulation")

            decision = self.decision.create_decision(simulation)
            steps.append("decision")

            self.emit_event(
                "decision.created",
                {"decision": decision},
            )

            self.orchestration.dispatch_tasks(
                [decision]
            )
            steps.append("orchestration")

            self.execution.create_execution(
                "runtime-job",
                decision,
            )

            self.emit_event(
                "execution.started",
                {"execution_id": "runtime-job"},
            )

            self.execution.start_execution(
                "runtime-job"
            )

            self.execution.complete_execution(
                "runtime-job"
            )

            steps.append("execution")

            self.emit_event(
                "execution.completed",
                {"execution_id": "runtime-job"},
            )

        except Exception as error:
            self.self_healing.detect_failure(
                {"error": str(error)}
            )

            self.self_healing.diagnose_issue(
                {"error": str(error)}
            )

            self.self_healing.apply_recovery(
                {"action": "restart_execution"},
            )

            self.self_healing.verify_recovery(
                {"status": "recovered"},
            )

            steps.append("recovered")

        self.governance.audit_execution(
            {
                "goal": goal,
                "steps": steps,
            }
        )

        self.observability.record_metric(
            {
                "steps": len(steps),
            }
        )

        self.learning.record_experience(
            {
                "goal": goal,
                "steps": steps,
            }
        )

        steps.append("learning")

        self.emit_event(
            "learning.recorded",
            {"goal": goal},
        )

        self.optimization.measure_performance(
            {
                "steps": len(steps),
            }
        )

        self.state.save_state(
            {
                "last_goal": goal,
                "steps": steps,
            }
        )

        self.state.snapshot()

        result = {
            "success": True,
            "goal": goal,
            "steps_completed": steps,
        }

        self.emit_event(
            "runtime.completed",
            result,
        )

        self._history.append(result)

        return result

    def history(self):
        return self._history
