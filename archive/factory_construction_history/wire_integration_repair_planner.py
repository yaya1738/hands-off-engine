from pathlib import Path

target = Path("ai/factory/autonomous_integration_supervisor.py")

source = target.read_text()

if "FactoryAutonomousIntegrationRepairPlanner" in source:
    print({"status": "ALREADY_WIRED"})
    raise SystemExit

source = source.replace(
    "from ai.factory.autonomous_integration_diagnosis import FactoryAutonomousIntegrationDiagnosis",
    "from ai.factory.autonomous_integration_diagnosis import FactoryAutonomousIntegrationDiagnosis\nfrom ai.factory.autonomous_integration_repair_planner import FactoryAutonomousIntegrationRepairPlanner",
)

source = source.replace(
    "self.diagnosis = FactoryAutonomousIntegrationDiagnosis()",
    "self.diagnosis = FactoryAutonomousIntegrationDiagnosis()\n        self.repair_planner = FactoryAutonomousIntegrationRepairPlanner()",
)

source = source.replace(
    'report["diagnosis"] = self.diagnosis.diagnose(report)',
    'report["diagnosis"] = self.diagnosis.diagnose(report)\n            report["repair_plan"] = self.repair_planner.plan(report["diagnosis"])',
)

target.write_text(source)

print({
    "status": "REPAIR_PLANNER_WIRED",
    "target": str(target),
})
