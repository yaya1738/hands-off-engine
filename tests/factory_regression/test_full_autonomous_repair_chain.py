from ai.factory.autonomous_integration_supervisor import FactoryAutonomousIntegrationSupervisor

s = FactoryAutonomousIntegrationSupervisor()

report = {
    "status": "CHECKED",
    "components": {
        "improvement_orchestrator": True,
        "broken_component": False,
    },
    "missing": ["broken_component"],
    "healthy": False,
}

diagnosis = s.diagnosis.diagnose(report)
plan = s.repair_planner.plan(diagnosis)
approval = s.repair_approval.approve(plan)
execution = s.repair_execution_bridge.execute(approval)
checkpoint = s.repair_checkpoint_adapter.record(execution)

print({
    "diagnosis": len(diagnosis["failures"]),
    "planned_repairs": len(plan["repairs"]),
    "approved_repairs": len(approval["repairs"]),
    "executed_repairs": len(execution["executed"]),
    "checkpoint": checkpoint["status"],
})
