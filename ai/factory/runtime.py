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
from ai.factory.assessment_bus_publisher import FactoryAssessmentBusPublisher
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
        self.assessment_publisher = FactoryAssessmentBusPublisher()

        self.improvement_planner = FactoryImprovementPlanner()

        self.improvement_queue = FactoryImprovementQueue()

        self.improvement_orchestrator = FactoryImprovementOrchestrator(

            assessor=self.improvement_assessment,
            planner=self.improvement_planner,
            queue=self.improvement_queue,
            assessment_publisher=self.assessment_publisher,
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