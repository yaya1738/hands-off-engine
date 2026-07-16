from typing import Any, Dict, List

from ai.factory.runtime_governance import FactoryRuntimeGovernance
from ai.factory.runtime_observability import FactoryRuntimeObservability
from ai.factory.runtime_state import FactoryRuntimeState

from ai.factory.event_bus import FactoryEventBus
from ai.factory.event_replay import FactoryEventReplay

from ai.factory.diagnostic_intelligence import FactoryDiagnosticIntelligence
from ai.factory.recommendation_feedback import FactoryRecommendationFeedback
from ai.factory.meta_optimizer import FactoryMetaOptimizer
from ai.factory.strategy_manager import FactoryStrategyManager
from ai.factory.goal_management import FactoryGoalManagement
from ai.factory.goal_optimizer import FactoryGoalOptimizer
from ai.factory.goal_genesis import FactoryGoalGenesis
from ai.factory.resource_allocator import FactoryResourceAllocator

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

        self.diagnostics = FactoryDiagnosticIntelligence()
        self.recommendations = FactoryRecommendationFeedback()
        self.meta_optimizer = FactoryMetaOptimizer()

        self.strategy_manager = FactoryStrategyManager()

        self.goal_management = FactoryGoalManagement()
        self.goal_optimizer = FactoryGoalOptimizer(
            self.goal_management
        )
        self.goal_genesis = FactoryGoalGenesis()
        self.strategy_manager.strategy_registry(
            "default",
            {
                "mode": "baseline",
            },
        )

        self.resource_allocator = FactoryResourceAllocator()
        self.resource_allocator.resource_registry(
            "runtime_compute",
            {
                "capacity": 1,
                "type": "default",
            },
        )

        self.self_healing = FactorySelfHealingIntelligence()

        self.planning = FactoryPlanningIntelligence()
        self.simulation = FactorySimulationIntelligence()
        self.decision = FactoryDecisionIntelligence()
        self.orchestration = FactoryOrchestrationIntelligence()
        self.execution = FactoryExecutionIntelligence()
        self.learning = FactoryLearningIntelligence()
        self.optimization = FactoryOptimizationIntelligence()

        self._history: List[Dict[str, Any]] = []

    def emit_event(self, event_type, payload):
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

    def manage_strategy(self, result):
        self.strategy_manager.evaluate_strategy(
            "default",
        )

        self.strategy_manager.strategy_performance(
            "default",
        )

        self.strategy_manager.activate_strategy(
            "default",
        )

        return {
            "strategy": "default",
            "runtime_success": result.get("success"),
        }

    def manage_resources(self, result):
        estimate = self.resource_allocator.estimate_cost(
            result
        )

        allocation = self.resource_allocator.allocate_resources(
            result,
            amount=estimate.get("cost", 1),
        )

        self.resource_allocator.rebalance(
            [
                allocation,
            ]
        )

        efficiency = self.resource_allocator.measure_efficiency(
            result
        )

        return {
            "estimate": estimate,
            "allocation": allocation,
            "efficiency": efficiency,
        }

    def run_improvement_cycle(self, result):
        analysis = self.diagnostics.analyze_execution(
            result
        )

        self.diagnostics.detect_failure_patterns(
            result.get("steps_completed", [])
        )

        self.diagnostics.explain_run(
            result.get("steps_completed", [])
        )

        recommendation = self.diagnostics.generate_recommendations(
            analysis
        )

        self.recommendations.collect_recommendations(
            recommendation
        )

        scored = self.meta_optimizer.score_improvement(
            recommendation
        )

        self.meta_optimizer.compare_strategies(
            [recommendation]
        )

        selected = self.meta_optimizer.select_best_action(
            [scored]
        )

        self.recommendations.apply_improvement(
            {
                "source": "meta_optimizer",
                "selected": selected,
            }
        )

        self.meta_optimizer.measure_roi(
            {
                "result": result,
            }
        )

    def submit_goal(self, objective):
        goal = {
            "objective": objective,
            "priority": 1,
            "source": "runtime",
            "status": "active",
        }

        created = self.goal_management.create_goal(
            goal
        )

        priority = self.goal_management.prioritize_goals()

        optimized = self.goal_optimizer.select_best()

        self.emit_event(
            "goal.submitted",
            {
                "created": created,
                "priority": priority,
                "optimized": optimized,
            },
        )

        return {
            "goal": goal,
            "priority": priority,
            "optimized": optimized,
        }

    def execute(self, goal):
        submitted = self.submit_goal(goal)
        goal = submitted["goal"]

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

        except Exception as error:
            self.self_healing.detect_failure(
                {"error": str(error)}
            )

            self.self_healing.diagnose_issue(
                {"error": str(error)}
            )

            steps.append("recovered")

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

        self.run_improvement_cycle(result)

        candidate_goal = self.goal_genesis.generate_goal(
            {
                "objective": "Optimize runtime improvement loop",
            }
        )

        self.emit_event(
            "goal.generated",
            {
                "goal": candidate_goal,
            },
        )

        strategy_result = self.manage_strategy(result)
        self.emit_event(
            "strategy.evaluated",
            strategy_result,
        )

        resource_result = self.manage_resources(result)
        self.emit_event(
            "resources.evaluated",
            resource_result,
        )

        self.emit_event(
            "runtime.completed",
            result,
        )

        self.goal_management.complete_goal(
            goal
        )

        self.emit_event(
            "goal.completed",
            {
                "goal": goal,
            },
        )

        self._history.append(result)

        return result

    def history(self):
        return self._history
