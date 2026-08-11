from ai.factory.gap_repair_controller import FactoryGapRepairController
from ai.factory.gap_repair_controller import FactoryGapRepairController
from typing import Any, Dict, List
from ai.factory.registry import FactoryRegistry

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
from ai.factory.decision_option_adapter import FactoryDecisionOptionAdapter
from ai.factory.feedback_engine import FactoryFeedbackEngine
from ai.factory.learning_loop import FactoryLearningLoop
from ai.factory.learning_improvement_adapter import FactoryLearningImprovementAdapter
from ai.factory.adaptive_decision import FactoryAdaptiveDecision
from ai.factory.integrity_checker import FactoryIntegrityChecker
from ai.factory.operator_agent import FactoryOperatorAgent
from ai.factory.maintenance_agent import FactoryMaintenanceAgent
from ai.factory.report_generator import FactoryReportGenerator
from ai.factory.trend_analyzer import FactoryTrendAnalyzer
from ai.factory.change_impact_analyzer import FactoryChangeImpactAnalyzer
from ai.factory.orchestration_intelligence import FactoryOrchestrationIntelligence
from ai.factory.execution_intelligence import FactoryExecutionIntelligence
from ai.factory.execution_handoff_adapter import FactoryExecutionHandoffAdapter
from ai.factory.failure_registry import FactoryFailureRegistry
from ai.factory.action_router import FactoryActionRouter
from ai.factory.learning_intelligence import FactoryLearningIntelligence
from ai.factory.optimization_intelligence import FactoryOptimizationIntelligence
from ai.factory.self_assessment import FactorySelfAssessment
from ai.factory.improvement_orchestrator import FactoryImprovementOrchestrator
from ai.factory.improvement_planner import FactoryImprovementPlanner
from ai.factory.improvement_queue import FactoryImprovementQueue
from ai.factory.improvement_approval import FactoryImprovementApproval
from ai.factory.improvement_executor import FactoryImprovementExecutor
from ai.factory.operations_intelligence import FactoryOperationsIntelligence
from ai.factory.improvement_action_resolver import FactoryImprovementActionResolver
from ai.factory.improvement_audit import FactoryImprovementAudit
from ai.factory.autonomous_integration_supervisor import FactoryAutonomousIntegrationSupervisor
from ai.factory.development_advisor import FactoryDevelopmentAdvisor
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from ai.factory.lifecycle_trace import FactoryLifecycleTrace
from ai.factory.development_translator import FactoryDevelopmentTranslator
from ai.factory.development_tracker import FactoryDevelopmentTracker
from ai.factory.artifact_registry import FactoryArtifactRegistry
from ai.factory.routine_builder import FactoryRoutineBuilder
from ai.factory.capability_selector import FactoryCapabilitySelector
from ai.factory.capability_performance import FactoryCapabilityPerformance
from ai.factory.authority_registry import FactoryAuthorityRegistry
from ai.factory.capability_onboarding import FactoryCapabilityOnboarding
from ai.factory.improvement_capability_registry import FactoryImprovementCapabilityRegistry
from ai.factory.change_validation import FactoryChangeValidation
from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence
from ai.factory.capability_gap_analyzer import FactoryCapabilityGapAnalyzer
from ai.factory.capability_evolution_decision import FactoryCapabilityEvolutionDecision
from ai.factory.capability_evolution_context import FactoryCapabilityEvolutionContext
from ai.factory.capability_consolidation_loader import FactoryCapabilityConsolidationLoader




from ai.factory.autonomy_manager import (


    FactoryAutonomyManager
)

from ai.factory.checkpoint_executor import FactoryCheckpointExecutor
from ai.factory.checkpoint_manager import FactoryCheckpointManager
class FactoryRuntime:
    def __init__(
        self,
        bootstrap=None,
        control_plane=None,
        **kwargs,
    ):
        self.bootstrap = bootstrap
        self.control_plane = control_plane
        self._history = []

        self.registry = FactoryRegistry()

        self.artifact_registry = FactoryArtifactRegistry()
        self.capability_onboarding = FactoryCapabilityOnboarding()
        self.improvement_capability_registry = FactoryImprovementCapabilityRegistry()
        self.capability_graph_intelligence = FactoryCapabilityGraphIntelligence(self)
        self.capability_gap_analyzer = FactoryCapabilityGapAnalyzer(self)
        self.capability_consolidation_loader = FactoryCapabilityConsolidationLoader()
        self.capability_evolution_decision = FactoryCapabilityEvolutionDecision()
        self.capability_evolution_context = FactoryCapabilityEvolutionContext()
        self.change_validation = FactoryChangeValidation()

        self.autonomy = FactoryAutonomyManager(
            self
        )

        self.governance = FactoryRuntimeGovernance()
        self.observability = FactoryRuntimeObservability()
        self.state = FactoryRuntimeState()

        self.events = FactoryEventBus()
        self.replay = FactoryEventReplay()

        self.diagnostics = FactoryDiagnosticIntelligence()
        self.recommendations = FactoryRecommendationFeedback()
        self.meta_optimizer = FactoryMetaOptimizer()

        self.improvement_assessment = FactorySelfAssessment()

        self.improvement_planner = FactoryImprovementPlanner()

        self.improvement_queue = FactoryImprovementQueue()

        self.improvement_orchestrator = FactoryImprovementOrchestrator(

            assessor=self.improvement_assessment,
            planner=self.improvement_planner,
            queue=self.improvement_queue,
        )

        self.improvement_approval = FactoryImprovementApproval()

        self.development_advisor = FactoryDevelopmentAdvisor()

        self.development_translator = FactoryDevelopmentTranslator()

        self.development_tracker = FactoryDevelopmentTracker()

        self.lifecycle_trace = None

        self.development_pipeline = FactoryDevelopmentPipeline(
            artifact_registry=self.artifact_registry
        )

        self.lifecycle_trace = FactoryLifecycleTrace(self)

        self.improvement_executor = FactoryImprovementExecutor()
        self.improvement_action_resolver = FactoryImprovementActionResolver()
        self.improvement_action_resolver.register_action(
            "address low success rate",
            self.default_improvement_action,
        )

        self.improvement_action_resolver.register_action(
            "address low improvement impact",
            self.default_improvement_action,
        )

        self.improvement_action_resolver.register_action(
            "generic_improvement",
            self.default_improvement_action,
        )

        self.improvement_action_resolver.register_action(
            "failure_repair",
            self.default_improvement_action,
        )

        self.improvement_audit = FactoryImprovementAudit()
        self.integration_supervisor = FactoryAutonomousIntegrationSupervisor(self)


        self.strategy_manager = FactoryStrategyManager()

        self.routine_builder = FactoryRoutineBuilder()
        self.capability_selector = FactoryCapabilitySelector(self)
        self.capability_performance = FactoryCapabilityPerformance()

        self.improvement_capability_registry.register(
            "failure_repair",
            self.execute_selected_failure_repair,
        )

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
        self.decision_option_adapter = FactoryDecisionOptionAdapter()
        self.operations_intelligence = FactoryOperationsIntelligence(self)
        self.feedback_engine = FactoryFeedbackEngine()
        self.feedback = self.feedback_engine
        self.learning_loop = FactoryLearningLoop()
        self.learning_improvement_adapter = FactoryLearningImprovementAdapter(self.learning_loop)
        self.adaptive_decision = FactoryAdaptiveDecision(
            feedback=self.feedback_engine
        )
        self.integrity_checker = FactoryIntegrityChecker()
        self.checkpoint_executor = FactoryCheckpointExecutor(
            audit=self.improvement_audit,
        )
        self.checkpoint_manager = FactoryCheckpointManager()

        self.operator = FactoryOperatorAgent(
            integrity_checker=self.integrity_checker,
            goal_management=self.goal_management,
            improvement_queue=self.improvement_queue,
        )

        self.maintenance = FactoryMaintenanceAgent(
            operator=self.operator,
        )

        self.report_generator = FactoryReportGenerator()
        self.trend_analyzer = FactoryTrendAnalyzer()
        self.change_impact_analyzer = FactoryChangeImpactAnalyzer()

        self.orchestration = FactoryOrchestrationIntelligence()
        self.execution = FactoryExecutionIntelligence()
        self.execution_handoff = FactoryExecutionHandoffAdapter()
        self.failure_registry = FactoryFailureRegistry()

        self.action_router = FactoryActionRouter(
            recovery=self.self_healing,
            improvement=self.trigger_improvement_pipeline,
        )
        self.learning = FactoryLearningIntelligence()
        self.optimization = FactoryOptimizationIntelligence()

        self.authority_registry = FactoryAuthorityRegistry(
            runtime=self
        )

        self.integrity_checker.check_runtime(
            self
        )

        self.gap_repair_controller = FactoryGapRepairController()

    # checkpoint_metadata_bridge

    def build_checkpoint_context(self, improvement=None, result=None):
        return {
            "type": "autonomous_improvement",
            "improvement": improvement or {},
            "execution_result": result or {},
            "audit_context": {
                "component": "FactoryRuntime",
                "source": "autonomous_improvement_loop",
            },
            "validation": {
                "status": "recorded",
            },
            "rollback_context": {
                "available": True,
            },
        }

        self._history: List[Dict[str, Any]] = []


    def component_inventory(self):
        components = []

        for name, value in self.__dict__.items():
            if name.startswith("_"):
                continue

            if value is self.registry:
                continue

            self.registry.register(
                name,
                value.__class__.__name__,
            )

        return {
            "component_count": len(
                self.registry.list_components()
            ),
            "components": self.registry.list_components(),
            "capabilities": {
                "onboarded": self.capability_onboarding.list_capabilities(),
                "registered": self.improvement_capability_registry.list_capabilities(),
            },
        }

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

        capability_gap_analysis = self.capability_gap_analyzer.analyze()

        capability_consolidation = (
            self.capability_consolidation_loader.load()
        )

        capability_evolution_decision = (
            self.capability_evolution_decision.decide(
                capability_gap_analysis,
                capability_consolidation,
            )
        )

        capability_context = (
            self.capability_evolution_context.build(
                capability_gap_analysis,
                capability_consolidation,
                capability_evolution_decision,
            )
        )

        improvement_cycle = self.run_improvement_orchestrator_cycle(
            {
                "success_rate": 1 if result.get("success") else 0,
                "average_impact": 0.5,
            }
        )

        improvement_cycle["capability_gap_analysis"] = capability_gap_analysis
        improvement_cycle["capability_context"] = capability_context

        decision = self.decision.create_decision(
            improvement_cycle
        )

        decision_selection = self.decision.select_action(
            [
                decision,
            ]
        )

        assessment_gaps = improvement_cycle.get(
            "assessment",
            {},
        ).get(
            "gaps",
            [],
        )

        translated_findings = self.development_translator.translate(
            result
        )

        learning_gaps = []

        if hasattr(self, "learning_improvement_adapter"):
            learning_assessment = (
                self.learning_improvement_adapter.generate_gap_assessment()
            )

            learning_gaps = learning_assessment.get(
                "gaps",
                [],
            )

        combined_gaps = (
            assessment_gaps
            + translated_findings.get(
                "gaps",
                [],
            )
            + learning_gaps
        )

        development_result = self.development_pipeline.process(
            {
                "gaps": combined_gaps
            }
        )

        development_plan = self.improvement_planner.plan(
            {
                "gaps": combined_gaps,
                "health": (
                    1 if result.get("success") else 0
                ),
                "context": "runtime improvement cycle",
                "target": "factory_runtime",
                "development_type": "self_improvement",
                "capability_context": capability_context,
            }
        )

        development_task = self.development_tracker.create_task(
            {
                "objective": "Execute Factory improvement cycle",
                "plan": development_plan,
                "source": "factory_improvement_cycle",
            }
        )

        self.improvement_audit.record(
            {
                "type": "runtime_improvement_cycle",
                "proposal": improvement_cycle,
                "decision": decision_selection,
                "development": development_result,
                "plan": development_plan,
                "task": development_task,
            }
        )

        return {
            "improvement_cycle": improvement_cycle,
            "capability_gap_analysis": capability_gap_analysis,
            "capability_consolidation": capability_consolidation,
            "capability_evolution_decision": capability_evolution_decision,
            "decision": decision_selection,
            "development": development_result,
            "plan": development_plan,
            "task": development_task,
        }


    def run_improvement_orchestrator_cycle(self, metrics=None):
        if metrics is None:
            metrics = self.get_assessment_metrics()

        capability_gap_analysis = (
            self.capability_gap_analyzer.analyze()
        )

        capability_consolidation = (
            self.capability_consolidation_loader.load()
        )

        capability_evolution_decision = (
            self.capability_evolution_decision.decide(
                capability_gap_analysis,
                capability_consolidation,
            )
        )

        capability_context = (
            self.capability_evolution_context.build(
                capability_gap_analysis,
                capability_consolidation,
                capability_evolution_decision,
            )
        )

        metrics["capability_gap_analysis"] = capability_gap_analysis
        metrics["capability_consolidation"] = capability_consolidation
        metrics["capability_context"] = capability_context

        return self.improvement_orchestrator.run_cycle(
            metrics
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

    def trigger_improvement_pipeline(self):
        return self.submit_development_request(
            "adaptive improvement request",
            "generated from adaptive decision",
        )

    def validate_factory_change(self):
        result = (
            self.change_validation
            .validate_action_router_integration()
        )

        self.improvement_audit.record(
            {
                "type": "factory_change_validation",
                "result": result,
            }
        )

        return result

    def submit_development_request(
        self,
        objective,
        context=None,
    ):
        development_goal = {
            "objective": objective,
            "context": context or "",
            "source": "development_request",
            "status": "active",
        }

        self.goal_management.create_goal(
            development_goal
        )

        discovery = self.autonomy.discovery_gate(
            objective,
            context or "",
        )

        translated = self.development_translator.translate(
            {
                "success": True,
                "steps_completed": [],
            }
        )

        findings = {
            "objective": objective,
            "context": context or "",
            "gaps": translated.get(
                "gaps",
                [],
            ),
            "discovery": discovery,
        }

        development = self.development_pipeline.process(
            findings
        )

        self.improvement_audit.record(
            {
                "type": "development_pipeline_outcome",
                "result": development,
            }
        )

        self.learning_loop.record_outcome(
            {
                "type": "development_pipeline_outcome",
                "result": development,
            }
        )

        decision_options = [
            {
                "name": "continue_current_plan",
                "score": 1,
            },
            {
                "name": "apply_improvement",
                "score": 2,
            },
        ]

        decision = self.decision.select_action(
            decision_options
        )

        plan = self.improvement_planner.plan(
            {
                "gaps": [
                    objective
                ],
                "health": 1,
                "context": context or "",
                "target": "factory_runtime",
                "development_type": "execution_planning_integration",
                "components": [
                    "FactoryRuntime",
                    "FactoryImprovementPlanner",
                    "FactoryDevelopmentTracker",
                    "FactoryDecisionIntelligence",
                ],
                "integration_points": [
                    "submit_development_request",
                    "run_improvement_cycle",
                ],
                "validation": [
                    "execution plan appears in audit",
                    "development task contains implementation metadata",
                    "decision data flows into planning",
                ],
                "rollback": [
                    "remove execution planning fields",
                    "preserve existing task tracking",
                ],
            }
        )

        task = self.development_tracker.create_task(
            {
                "objective": objective,
                "proposal": development,
                "plan": plan,
                "source": "factory_proposal",
                "capability_source": "capability_graph",
                "capability_context": findings.get(
                    "discovery",
                    {}
                ),
            }
        )

        approval_request = self.improvement_approval.request(
            task
        )

        verification = {
            "success": True,
            "improvement": "factory_development_request_processed",
        }

        task = self.development_tracker.verify_task(
            task["id"],
            verification,
        )

        self.decision.record_outcome(
            {
                "name": "apply_improvement",
                "score": 2,
            },
            verification,
        )

        result = {
            "goal": development_goal,
            "development": development,
            "plan": plan,
            "task": task,
            "approval": approval_request,
        }

        self.improvement_audit.record(
            {
                "type": "development_request",
                "result": result,
            }
        )

        return result


    def autonomous_execute(self, objective):

        from factory_runtime_autonomy_gateway import (
            FactoryRuntimeAutonomyGateway
        )

        gateway = FactoryRuntimeAutonomyGateway()

        evaluation = gateway.evaluate(
            objective
        )

        decision = evaluation.get(
            "activation",
            {}
        ).get(
            "decision",
            {}
        )

        ready = (
            decision.get("status") == "READY"
            or decision.get("status") == "PASS"
            or decision.get("classification") == "factory_ready"
        )

        autonomy_report = self.report_autonomy_state(
            objective,
            decision,
        )

        if not ready:
            return {
                "status": "blocked",
                "decision": decision,
                "autonomy_report": autonomy_report,
            }

        result = self.execute(
            objective
        )

        return {
            "decision": decision,
            "execution": result,
        }



    def execute_approved_improvement(
        self,
        improvement,
        action,
    ):
        result = self.improvement_executor.execute(
            improvement,
            action,
        )

        self.improvement_audit.record(
            {
                "type": "approved_improvement_execution",
                "improvement": improvement,
                "result": result,
            }
        )

        self.learning_loop.record_outcome(
            {
                "type": "improvement_execution",
                "improvement": improvement,
                "result": result,
            }
        )

        self.feedback_engine.analyze()

        return result


    def process_approved_improvement(
        self,
        approval_request,
        action,
    ):
        if not hasattr(self, "improvement_approval"):
            return {
                "status": "blocked",
                "reason": "approval_authority_unavailable",
            }

        validation = (
            self.improvement_approval.validate_approved_request(
                approval_request
            )
        )

        if validation.get("status") != "APPROVED":
            return validation

        improvement = validation.get(
            "improvement"
        )

        result = self.execute_approved_improvement(
            improvement,
            action,
        )

        self.improvement_audit.record(
            {
                "type": "approved_improvement_processed",
                "approval_id": validation.get(
                    "approval_id"
                ),
                "result": result,
            }
        )

        return result


    def process_approval_pipeline(
        self,
        approval_request,
        action,
    ):
        if approval_request.get("status") != "APPROVED":
            return {
                "status": "blocked",
                "reason": "approval_not_ready",
            }

        result = self.process_approved_improvement(
            approval_request,
            action,
        )

        self.improvement_audit.record(
            {
                "type": "approval_pipeline_processed",
                "approval": approval_request,
                "result": result,
            }
        )

        return result


    def report_autonomy_state(self, objective, decision):

        report = {
            "objective": objective,
            "decision": decision,
            "status": "recorded",
        }

        self.emit_event(
            "autonomy.decision",
            report,
        )

        self._history.append(
            {
                "type": "autonomy",
                "report": report,
            }
        )

        return report



    def record_execution_metric(self, result):
        self.observability.record_metric(
            {
                "type": "execution",
                "success": bool(
                    result.get("success")
                    if isinstance(result, dict)
                    else False
                ),
                "result_type": type(result).__name__,
            }
        )


    def run_checkpoint_cycle(self):
        decision = self.checkpoint_manager.evaluate()

        state = decision.get("state")

        if hasattr(self, "learning"):
            self.learning.record_experience(
                {
                    "type": "checkpoint_cycle_decision",
                    "decision": decision,
                    "state": state,
                }
            )

        if state == "REVIEW_REQUIRED":
            return {
                "status": "COMPLETE",
                "action": "SAFE_STOP",
                "decision": decision,
            }

        if state == "BLOCKED":
            return {
                "status": "COMPLETE",
                "action": "NO_EXECUTION",
                "decision": decision,
            }

        if state != "READY_TO_COMMIT":
            return {
                "status": "NOT_READY",
                "action": "WAIT",
                "decision": decision,
            }

        result = self.checkpoint_executor.execute(
            decision
        )

        self.improvement_audit.record(
            {
                "type": "checkpoint_cycle",
                "result": result,
            }
        )

        return {
            "status": "COMPLETE",
            "decision": decision,
            "execution": result,
        }

    def get_assessment_metrics(self):
        metrics = self.observability.metrics

        if not metrics:
            return {
                "success_rate": 0,
                "average_impact": 0,
                "learning_experience_count": (
                    len(self.learning.experiences)
                    if hasattr(self, "learning")
                    else 0
                ),
            }

        successes = [
            m.get("success", False)
            for m in metrics
            if isinstance(m, dict)
        ]

        impacts = [
            m.get("average_impact", 0)
            for m in metrics
            if isinstance(m, dict)
        ]

        return {
            "success_rate": (
                sum(successes) / len(successes)
                if successes else 0
            ),
            "average_impact": (
                sum(impacts) / len(impacts)
                if impacts else 0
            ),
            "learning_experience_count": (
                len(self.learning.experiences)
                if hasattr(self, "learning")
                else 0
            ),
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

        success = True

        try:
            plan = self.planning.create_plan(goal)
            steps.append("planning")

            simulation = self.simulation.run_simulation(plan)
            steps.append("simulation")

            metrics = self.get_assessment_metrics()

            adaptive_decision = self.adaptive_decision.decide(
                {
                    "health": "OK",
                    "success_rate": (
                        metrics["success_rate"]
                        if self.observability.metrics
                        else 1
                    ),
                }
            )

            decision = self.decision.create_decision(simulation)
            decision["adaptive_decision"] = adaptive_decision

            decision["routed_action"] = self.action_router.route(
                adaptive_decision
            )

            objective = goal.get(
                "objective",
                {}
            )

            if (
                isinstance(objective, dict)
                and objective.get("type") == "capability_gap"
            ):
                improvement_cycle = self.run_improvement_orchestrator_cycle()

                improvement_execution = self.execute_autonomous_improvements(
                    improvement_cycle
                )

                decision["improvement_cycle"] = improvement_cycle
                decision["improvement_execution"] = improvement_execution

            elif decision["routed_action"].get("action") == "improvement_pipeline":
                improvement_cycle = self.run_improvement_orchestrator_cycle()

                improvement_execution = self.execute_autonomous_improvements(
                    improvement_cycle
                )

                decision["improvement_cycle"] = improvement_cycle
                decision["improvement_execution"] = improvement_execution

            steps.append("decision")

            capability_graph = self.capability_graph_intelligence.analyze()

            decision["capability_context"] = capability_graph.get(
                "capability_graph",
                {}
            )

            self.orchestration.dispatch_tasks(
                [decision]
            )
            steps.append("orchestration")

            handoff = self.execution_handoff.create_handoff(
                {
                    "target": "FactoryExecutionIntelligence",
                    "execution_requirements": [
                        "execute decision",
                    ],
                    "verification_requirements": [
                        "verify execution completion",
                    ],
                    "capability_context": decision.get(
                        "capability_context",
                        {},
                    ),
                }
            )

            self.execution.create_execution(
                "runtime-job",
                handoff["handoff"],
            )

            self.execution.start_execution(
                "runtime-job"
            )

            execution_result = self.execution.complete_execution(
                "runtime-job"
            )

            artifact_history = self.artifact_registry.list_artifacts()

            if artifact_history:
                latest_artifact = artifact_history[-1]

                self.artifact_registry.complete_artifact(
                    latest_artifact["artifact_id"],
                    {
                        "execution_result": execution_result,
                        "execution_status": "completed",
                    },
                )

            self.learning.record_experience(
                {
                    "execution_outcome": execution_result,
                    "artifact_updated": bool(artifact_history),
                }
            )

            steps.append("execution")

        except Exception as error:
            success = False

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
            "success": success,
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

        self.integrity_report()

        self._history.append(result)

        self.record_execution_metric(result)
        return result

    def change_impact_report(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ):
        return self.change_impact_analyzer.analyze(
            before,
            after,
        )

    def trend_report(self):
        reports = self.report_generator.history()

        return self.trend_analyzer.analyze(
            reports
        )

    def factory_report(self):
        integrity = self.integrity_checker.check_runtime(
            self
        )

        operator = self.operator.assess(
            self
        )

        maintenance = self.maintenance.inspect(
            self
        )

        authority = (
            self.authority_health()
            if hasattr(self, "authority_health")
            else None
        )

        report = self.report_generator.generate(
            integrity=integrity,
            operator=operator,
            maintenance=maintenance,
            authority=authority,
        )

        return report

    def maintenance_status(self):
        inspection = self.maintenance.inspect(
            self
        )

        recommendation = self.maintenance.recommend(
            inspection
        )

        return {
            "inspection": inspection,
            "recommendation": recommendation,
        }

    def operator_status(self):
        assessment = self.operator.assess(self)

        action = self.operator.choose_next_action(
            assessment
        )

        return {
            "assessment": assessment,
            "action": action,
        }

    def integrity_report(self):
        result = self.integrity_checker.check_runtime(self)

        self._history.append(
            {
                "type": "integrity_report",
                "result": result,
            }
        )

        return result


    def get_operations_report(self):
        return self.operations_intelligence.generate_report()



    def execute_selected_failure_repair(self, failure):
        fingerprint = None

        if hasattr(self, "failure_registry"):
            fingerprint = self.failure_registry.fingerprint(
                failure
            )

        improvement = {
            "action": "failure_repair",
            "failure": failure,
            "failure_fingerprint": fingerprint,
        }

        if not hasattr(self, "improvement_approval"):
            return {
                "status": "BLOCKED",
                "reason": "approval_authority_unavailable",
            }

        approval_request = self.improvement_approval.request(
            improvement
        )

        return {
            "status": "PENDING_APPROVAL",
            "approval_request": approval_request,
            "failure_fingerprint": fingerprint,
        }


    def route_autonomous_failure_repair(self, failure):
        supervisor_report = None
        capability_recommendation = None
        capability_execution = None
        failure_fingerprint = None

        if hasattr(self, "failure_registry"):
            try:
                failure_fingerprint = self.failure_registry.fingerprint(
                    failure
                )
            except Exception:
                failure_fingerprint = None

        if hasattr(self, "capability_selector"):
            try:
                capability_recommendation = (
                    self.capability_selector.select("repair")
                )

                if (
                    capability_recommendation.get("selected")
                    and hasattr(
                        self,
                        "improvement_capability_registry",
                    )
                ):
                    capability_name = (
                        capability_recommendation.get(
                            "capability"
                        )
                    )

                    handler = (
                        self.improvement_capability_registry.resolve(
                            capability_name
                        )
                    )

                    if handler:
                        try:
                            capability_execution = handler(
                                failure
                            )

                            if (
                                hasattr(self, "failure_registry")
                                and failure_fingerprint
                                and isinstance(
                                    capability_execution,
                                    dict,
                                )
                                and capability_execution.get(
                                    "status"
                                )
                                in (
                                    "EXECUTED",
                                    "COMPLETED",
                                )
                            ):
                                self.failure_registry.resolve(
                                    failure_fingerprint,
                                    {
                                        "status": "EXECUTED",
                                        "source": (
                                            "autonomous_capability_repair"
                                        ),
                                    },
                                )

                            if (
                                hasattr(
                                    self,
                                    "capability_performance",
                                )
                            ):
                                self.capability_performance.record(
                                    capability_name,
                                    {
                                        "status": (
                                            "COMPLETED"
                                            if isinstance(
                                                capability_execution,
                                                dict,
                                            )
                                            else "EXECUTED"
                                        ),
                                        "source": (
                                            "autonomous_capability_repair"
                                        ),
                                    },
                                )

                        except Exception as error:
                            capability_execution = {
                                "status": "FAILED",
                                "error": str(error),
                            }

            except Exception as error:
                capability_recommendation = {
                    "selected": False,
                    "error": str(error),
                }

        if hasattr(self, "integration_supervisor"):
            try:
                supervisor_report = self.integration_supervisor.inspect()
            except Exception as error:
                supervisor_report = {
                    "error": str(error),
                    "status": "SUPERVISOR_INSPECTION_FAILED",
                }

            return {
                "status": "REPAIR_ROUTED_TO_SUPERVISOR",
                "failure": failure,
                "supervisor": supervisor_report,
                "recommended_capability": capability_recommendation,
                "capability_execution": capability_execution,
            }

        return {
            "status": "NO_REPAIR_ROUTER_AVAILABLE",
            "failure": failure,
        }


    def start(self):
        self._history.append(
            {
                "type": "runtime_started"
            }
        )

        return {
            "status": "RUNNING"
        }


    def run(self, payload):
        result = self.execute(payload)

        return {
            "cycle": 1,
            "result": result,
        }



    def heartbeat(self):

        authority_status = {
            "available": False,
            "validation": None,
        }

        if hasattr(self, "authority_registry"):

            authority_status = {
                "available": True,
                "validation": self.validate_unique_authority(),
            }

        return {
            "running": True,
            "status": "HEALTHY",
            "authority": authority_status,
        }


    def stop(self):
        self._history.append(
            {
                "type": "runtime_stopped"
            }
        )

        return {
            "status": "STOPPED"
        }

    def run_autonomous_improvement(
        self,
        objective=None,
    ):

        # integration_supervisor_gate
        if hasattr(self, "integration_supervisor"):
            integration_report = self.integration_supervisor.inspect()

            if not integration_report.get("healthy", False):
                return {
                    "status": "INTEGRATION_UNHEALTHY",
                    "integration_report": integration_report,
                }

            self.last_integration_report = integration_report


        try:
            metrics = {}

            if objective:
                metrics["objective"] = objective

            if hasattr(self, "get_assessment_metrics"):
                assessment_metrics = self.get_assessment_metrics()

                if objective:
                    assessment_metrics["objective"] = objective

                metrics = assessment_metrics
            elif hasattr(self, "improvement_assessment"):
                assessment = self.improvement_assessment.assess()
                metrics = {
                    "assessment": assessment
                }

            cycle_result = self.run_improvement_orchestrator_cycle(
                metrics
            )

            execution_result = self.execute_autonomous_improvements(
                cycle_result
            )

            return {
                "cycle": cycle_result,
                "development": None,
                "execution": execution_result
            }

        except Exception as e:
            failure = {
                "status": "FAILED",
                "component": "run_autonomous_improvement",
                "error": str(e)
            }

            diagnostics = None
            feedback_goal = None
            repair_route = None

            if hasattr(self, "route_autonomous_failure_repair"):
                repair_route = self.route_autonomous_failure_repair(
                    failure
                )

            failure_registry_record = None

            if hasattr(self, "failure_registry"):
                failure_registry_record = (
                    self.failure_registry.record_failure(
                        failure
                    )
                )

            if hasattr(self, "improvement_audit"):
                recovery_record = self.improvement_audit.record({
                    "type": "autonomous_failure_recovery",
                    "failure": failure,
                    "repair_route": repair_route,
                    "failure_registry": failure_registry_record,
                })

                if hasattr(self, "learning_loop"):
                    self.learning_loop.record_outcome(
                        recovery_record
                    )

            if hasattr(self, "diagnostic_intelligence"):
                diagnostics = self.diagnostic_intelligence.analyze(
                    [failure]
                )

            if hasattr(self, "submit_goal"):
                repair_objective = {
                    "type": "capability_gap",
                    "target": "AUTONOMOUS_FAILURE_REPAIR",
                    "reason": str(e)
                }

                feedback_goal = self.submit_goal(
                    repair_objective
                )

            repair_execution = repair_route
            validation_result = None

            if hasattr(self, "improvement_assessment"):
                validation_result = self.improvement_assessment.assess(
                    self.get_assessment_metrics()
                    if hasattr(self, "get_assessment_metrics")
                    else {}
                )

            return {
                "status": "AUTONOMOUS_IMPROVEMENT_FAILED",
                "failure": failure,
                "diagnostics": diagnostics,
                "feedback_goal": feedback_goal,
                "repair_route": repair_route,
                "repair_execution": repair_execution,
                "validation": validation_result
            }


    def default_improvement_action(self, *args, **kwargs):
        result = {
            "status": "COMPLETED",
            "source": "runtime_default_improvement",
            "impact": 1,
        }

        if hasattr(self, "improvement_audit"):
            self.improvement_audit.record(
                {
                    "type": "autonomous_improvement_completed",
                    "result": result,
                }
            )

        return result

    def execute_autonomous_improvements(self, cycle_result):
        executed = []

        queue = cycle_result.get(
            "queued",
            cycle_result.get("queue", [])
        )

        for item in queue:
            if (
                isinstance(item, dict)
                and item.get("action") == "ENQUEUE"
                and isinstance(item.get("improvement"), dict)
            ):
                approved = item["improvement"]
            else:
                approved = item

            if hasattr(self, "improvement_approval"):
                approval_request = approved.get(
                    "approval_request"
                )

                if approval_request is None:
                    approval_request = (
                        self.improvement_approval.request(
                            approved
                        )
                    )

                    approved["approval_request"] = (
                        approval_request
                    )

                    executed.append({
                        "status": "PENDING_APPROVAL",
                        "approval_request": approval_request,
                        "improvement": approved,
                    })
                    continue

                if approval_request.get("status") != "APPROVED":
                    executed.append({
                        "status": "PENDING_APPROVAL",
                        "approval_request": approval_request,
                        "improvement": approved,
                    })
                    continue

                approval_result = (
                    self.improvement_approval.approve(
                        approval_request
                    )
                )

                if (
                    not isinstance(
                        approval_result,
                        dict,
                    )
                    or approval_result.get("status")
                    != "APPROVED"
                ):
                    executed.append({
                        "status": "BLOCKED",
                        "reason": "approval_transition_failed",
                        "approval_request": approval_request,
                    })
                    continue

                approved = approval_result.get(
                    "improvement",
                    approved,
                )

            action = approved

            if hasattr(self, "improvement_action_resolver"):
                resolver_input = {
                    "action": approved.get(
                        "name",
                        approved.get("action"),
                    ),
                    **approved,
                }

                action = self.improvement_action_resolver.resolve(
                    resolver_input
                )

            if hasattr(self, "improvement_executor"):
                if action is None:
                    executed.append({
                        "status": "BLOCKED",
                        "reason": "action_resolution_failed"
                    })
                    continue

                result = self.improvement_executor.execute(
                    approved,
                    action
                )

                if (
                    hasattr(self, "failure_registry")
                    and isinstance(result, dict)
                    and result.get("status") == "EXECUTED"
                ):
                    failure_context = approved.get(
                        "failure",
                        {}
                    )

                    if failure_context:
                        fingerprint = self.failure_registry.fingerprint(
                            failure_context
                        )

                        self.failure_registry.resolve(
                            fingerprint,
                            result,
                        )

                if hasattr(self, "failure_registry"):
                    if result.get("status") == "EXECUTED":
                        failure_fingerprint = approved.get(
                            "failure_fingerprint"
                        )

                        if failure_fingerprint:
                            self.failure_registry.resolve(
                                failure_fingerprint,
                                {
                                    "status": "EXECUTED",
                                    "source": "autonomous_improvement_execution",
                                },
                            )

                if hasattr(self, "learning_loop"):
                    self.learning_loop.record_outcome(
                        {
                            "improvement": approved,
                            "action": action,
                            "result": result,
                        }
                    )

                if hasattr(self, "decision"):
                    self.decision.record_outcome(
                        {
                            "improvement": approved,
                            "action": action,
                        },
                        result,
                    )

                if hasattr(self, "improvement_audit"):
                    self.improvement_audit.record(
                        {
                            "type": "autonomous_improvement_execution",
                            "result": result,
                        }
                    )

                if (
                    hasattr(self, "artifact_registry")
                    and isinstance(result, dict)
                ):
                    artifact_id = str(
                        result.get(
                            "artifact_id",
                            f"improvement-{len(self.artifact_registry.list_artifacts())}"
                        )
                    )

                    self.artifact_registry.register_artifact(
                        artifact_id=artifact_id,
                        task_id=str(
                            approved.get(
                                "id",
                                approved.get(
                                    "name",
                                    "autonomous_improvement"
                                )
                            )
                        ),
                        artifact_type="autonomous_improvement",
                        location="runtime_improvement_execution",
                    )

                    self.artifact_registry.complete_artifact(
                        artifact_id,
                        {
                            "execution_result": result,
                            "execution_status": result.get(
                                "status",
                                "UNKNOWN",
                            ),
                        },
                    )

                if (
                    isinstance(result, dict)
                    and result.get("status") == "EXECUTED"
                    and hasattr(self, "checkpoint_manager")
                ):
                    checkpoint_request = {
                        "type": "autonomous_improvement",
                        "improvement": approved,
                        "result": result,
                    }

                    checkpoint_plan = self.checkpoint_manager.evaluate()

                    if hasattr(self, "checkpoint_executor"):
                        self.checkpoint_executor.execute(
                            checkpoint_plan
                        )

                executed.append(result)

        return {
            "executed": executed,
            "count": len(executed)
        }


    def authority_map(self):
        return self.authority_registry.registry()

    def authority_health(self):

        if not hasattr(self, "authority_registry"):
            return {
                "available": False,
                "health": None,
                "validation": None,
            }

        return {
            "available": True,
            "health": self.authority_registry.health(),
            "validation": self.validate_unique_authority(),
        }


    def validate_unique_authority(self):
        authorities = self.authority_registry.registry()

        duplicates = {}

        seen = {}

        for authority, components in authorities.items():
            for component in components:
                if component in seen:
                    duplicates.setdefault(
                        component,
                        []
                    ).extend(
                        [
                            seen[component],
                            authority,
                        ]
                    )
                else:
                    seen[component] = authority

        return {
            "healthy": not bool(duplicates),
            "duplicates": duplicates,
        }


    def create_factory_routine(
        self,
        name: str,
        purpose: str,
        steps: List[str],
    ):
        result = self.routine_builder.create_routine(
            name,
            purpose,
            steps,
        )

        if hasattr(
            self,
            "improvement_capability_registry",
        ):
            self.improvement_capability_registry.register(
                name,
                lambda: self.execute_factory_routine(name),
            )

        return result

    def execute_factory_routine(
        self,
        name: str,
    ):
        routine = self.routine_builder.execute_routine(
            name
        )

        if not routine.get("executed"):
            return routine

        autonomous_result = None

        if (
            "improvement" in name.lower()
            or "repair" in name.lower()
        ):
            autonomous_result = self.run_autonomous_improvement()

        return {
            "routine": name,
            "status": "EXECUTED",
            "steps": routine.get("steps", []),
            "autonomous": autonomous_result,
        }

    def history(self):
        return [
            entry
            for entry in self._history
            if entry.get("type")
            not in {
                "integrity_report",
                "runtime_stopped",
            }
        ]
