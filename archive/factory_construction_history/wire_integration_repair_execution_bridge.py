from pathlib import Path

target = Path("ai/factory/autonomous_integration_supervisor.py")

source = target.read_text()

if "FactoryAutonomousIntegrationRepairExecutionBridge" in source:
    print({"status": "ALREADY_WIRED"})
    raise SystemExit

source = source.replace(
    "from ai.factory.autonomous_integration_repair_approval import FactoryAutonomousIntegrationRepairApproval",
    "from ai.factory.autonomous_integration_repair_approval import FactoryAutonomousIntegrationRepairApproval\nfrom ai.factory.autonomous_integration_repair_execution_bridge import FactoryAutonomousIntegrationRepairExecutionBridge",
)

source = source.replace(
    "self.repair_approval = FactoryAutonomousIntegrationRepairApproval()",
    "self.repair_approval = FactoryAutonomousIntegrationRepairApproval()\n        self.repair_execution_bridge = FactoryAutonomousIntegrationRepairExecutionBridge()",
)

source = source.replace(
    'report["repair_approval"] = self.repair_approval.approve(report["repair_plan"])',
    'report["repair_approval"] = self.repair_approval.approve(report["repair_plan"])\n            report["repair_execution"] = self.repair_execution_bridge.execute(report["repair_approval"])',
)

target.write_text(source)

print({
    "status": "REPAIR_EXECUTION_BRIDGE_WIRED",
    "target": str(target),
})
