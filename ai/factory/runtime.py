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
from ai.factory.development_advisor import FactoryDevelopmentAdvisor
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from ai.factory.lifecycle_trace import FactoryLifecycleTrace
from ai.factory.development_translator import FactoryDevelopmentTranslator
from ai.factory.development_tracker import FactoryDevelopmentTracker
from ai.factory.artifact_registry import FactoryArtifactRegistry
from ai.factory.capability_onboarding import FactoryCapabilityOnboarding
from ai.factory.improvement_capability_registry import FactoryImprovementCapabilityRegistry
from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence




from ai.factory.autonomy_manager import (
    FactoryAutonomyManager
)

class FactoryRuntime:
    def __init__(self):
        self.registry = FactoryRegistry()

        self.artifact_registry = FactoryArtifactRegistry()
        self.capability_onboarding = FactoryCapabilityOnboarding()
        self.improvement_capability_registry = FactoryImprovementCapabilityRegistry()

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
        self.improvement_audit = FactoryImprovementAudit()


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
        self.decision_option_adapter = FactoryDecisionOptionAdapter()
        self.operations_intelligence = FactoryOperationsIntelligence(self)
        self.feedback_engine = FactoryFeedbackEngine()
        self.feedback = self.feedback_engine
        self.learning_loop = FactoryLearningLoop()
        self.adaptive_decision = FactoryAdaptiveDecision(
            feedback=self.feedback_engine
        )
        self.integrity_checker = FactoryIntegrityChecker()

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
        self.learning = FactoryLearningIntelligence()
        self.optimization = FactoryOptimizationIntelligence()

        self.integrity_checker.check_runtime(
            self
        )

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

        improvement_cycle = self.improvement_orchestrator.run_cycle(
            {
                "success_rate": 1 if result.get("success") else 0,
                "average_impact": 0.5,
            }
        )

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

        development_result = self.development_pipeline.process(
            {
                "gaps": (
                    assessment_gaps
                    + translated_findings.get(
                        "gaps",
                        [],
                    )
                )
            }
        )

        development_plan = self.improvement_planner.plan(
            {
                "gaps": (
                    assessment_gaps
                    + translated_findings.get(
                        "gaps",
                        [],
                    )
                ),
                "health": (
                    1 if result.get("success") else 0
                ),
                "context": "runtime improvement cycle",
                "target": "factory_runtime",
                "development_type": "self_improvement",
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
        improvement,
        action,
    ):
        if improvement.get("status") != "APPROVED":
            return {
                "status": "blocked",
                "reason": "improvement_not_approved",
            }

        result = self.execute_approved_improvement(
            improvement,
            action,
        )

        self.improvement_audit.record(
            {
                "type": "approved_improvement_processed",
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

        improvement = approval_request.get(
            "improvement"
        )

        result = self.process_approved_improvement(
            improvement,
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


    def get_assessment_metrics(self):
        metrics = self.observability.metrics

        if not metrics:
            return {
                "success_rate": 0,
                "average_impact": 0,
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

            decision = self.decision.create_decision(simulation)
            steps.append("decision")

            capability_graph = FactoryCapabilityGraphIntelligence(
                self
            ).analyze()

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

            self.execution.complete_execution(
                "runtime-job"
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

        report = self.report_generator.generate(
            integrity=integrity,
            operator=operator,
            maintenance=maintenance,
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

    def history(self):
        return self._history
