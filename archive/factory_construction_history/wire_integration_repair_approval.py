from pathlib import Path

target = Path("ai/factory/autonomous_integration_supervisor.py")

source = target.read_text()

if "FactoryAutonomousIntegrationRepairApproval" in source:
    print({"status": "ALREADY_WIRED"})
    raise SystemExit

source = source.replace(
    "from ai.factory.autonomous_integration_repair_planner import FactoryAutonomousIntegrationRepairPlanner",
    "from ai.factory.autonomous_integration_repair_planner import FactoryAutonomousIntegrationRepairPlanner\nfrom ai.factory.autonomous_integration_repair_approval import FactoryAutonomousIntegrationRepairApproval",
)

source = source.replace(
    "self.repair_planner = FactoryAutonomousIntegrationRepairPlanner()",
    "self.repair_planner = FactoryAutonomousIntegrationRepairPlanner()\n        self.repair_approval = FactoryAutonomousIntegrationRepairApproval()",
)

source = source.replace(
    'report["repair_plan"] = self.repair_planner.plan(report["diagnosis"])',
    'report["repair_plan"] = self.repair_planner.plan(report["diagnosis"])\n            report["repair_approval"] = self.repair_approval.approve(report["repair_plan"])',
)

target.write_text(source)

print({
    "status": "REPAIR_APPROVAL_WIRED",
    "target": str(target),
})
