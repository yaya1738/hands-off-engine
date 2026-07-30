from pathlib import Path

target = Path("ai/factory/autonomous_integration_supervisor.py")

source = target.read_text()

if "FactoryAutonomousRepairCheckpointAdapter" in source:
    print({"status": "ALREADY_WIRED"})
    raise SystemExit

source = source.replace(
    "from ai.factory.autonomous_integration_repair_execution_bridge import FactoryAutonomousIntegrationRepairExecutionBridge",
    "from ai.factory.autonomous_integration_repair_execution_bridge import FactoryAutonomousIntegrationRepairExecutionBridge\nfrom ai.factory.autonomous_repair_checkpoint_adapter import FactoryAutonomousRepairCheckpointAdapter",
)

source = source.replace(
    "self.repair_execution_bridge = FactoryAutonomousIntegrationRepairExecutionBridge()",
    "self.repair_execution_bridge = FactoryAutonomousIntegrationRepairExecutionBridge()\n        self.repair_checkpoint_adapter = FactoryAutonomousRepairCheckpointAdapter()",
)

source = source.replace(
    'report["repair_execution"] = self.repair_execution_bridge.execute(report["repair_approval"])',
    'report["repair_execution"] = self.repair_execution_bridge.execute(report["repair_approval"])\n            report["repair_checkpoint"] = self.repair_checkpoint_adapter.record(report["repair_execution"])',
)

target.write_text(source)

print({
    "status": "REPAIR_CHECKPOINT_ADAPTER_WIRED",
    "target": str(target),
})
