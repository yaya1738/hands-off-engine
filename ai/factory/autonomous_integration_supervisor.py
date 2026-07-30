
from typing import Any, Dict
from ai.factory.autonomous_integration_diagnosis import FactoryAutonomousIntegrationDiagnosis
from ai.factory.autonomous_integration_repair_planner import FactoryAutonomousIntegrationRepairPlanner
from ai.factory.autonomous_integration_repair_approval import FactoryAutonomousIntegrationRepairApproval
from ai.factory.autonomous_integration_repair_execution_bridge import FactoryAutonomousIntegrationRepairExecutionBridge
from ai.factory.autonomous_repair_checkpoint_adapter import FactoryAutonomousRepairCheckpointAdapter


class FactoryAutonomousIntegrationSupervisor:
    """
    Observational supervisor for autonomous improvement pipeline health.

    Initial version:
    - checks connectivity
    - reports missing boundaries
    - does not mutate runtime behavior
    """

    def __init__(self, runtime=None):
        self.runtime = runtime
        self._history = []
        self.diagnosis = FactoryAutonomousIntegrationDiagnosis()
        self.repair_planner = FactoryAutonomousIntegrationRepairPlanner()
        self.repair_approval = FactoryAutonomousIntegrationRepairApproval()
        self.repair_execution_bridge = FactoryAutonomousIntegrationRepairExecutionBridge()
        self.repair_checkpoint_adapter = FactoryAutonomousRepairCheckpointAdapter()

    def inspect(self) -> Dict[str, Any]:
        report = {
            "status": "CHECKED",
            "components": {},
            "missing": [],
        }

        checks = [
            "improvement_orchestrator",
            "improvement_queue",
            "improvement_action_resolver",
            "improvement_executor",
            "development_pipeline",
            "improvement_audit",
            "checkpoint_manager",
        ]

        for component in checks:
            exists = hasattr(self.runtime, component) if self.runtime else False

            report["components"][component] = exists

            if not exists:
                report["missing"].append(component)

        report["healthy"] = len(report["missing"]) == 0

        if not report["healthy"]:
            report["diagnosis"] = self.diagnosis.diagnose(report)
            report["repair_plan"] = self.repair_planner.plan(report["diagnosis"])
            report["repair_approval"] = self.repair_approval.approve(report["repair_plan"])
            report["repair_execution"] = self.repair_execution_bridge.execute(report["repair_approval"])
            report["repair_checkpoint"] = self.repair_checkpoint_adapter.record(report["repair_execution"])

        self._history.append(report)

        return report

    def history(self):
        return self._history
