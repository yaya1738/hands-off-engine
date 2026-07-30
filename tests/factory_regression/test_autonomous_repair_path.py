from ai.factory.autonomous_integration_supervisor import FactoryAutonomousIntegrationSupervisor

s = FactoryAutonomousIntegrationSupervisor()

fake_report = {
    "status": "CHECKED",
    "components": {
        "improvement_orchestrator": True,
        "broken_component": False,
    },
    "missing": ["broken_component"],
    "healthy": False,
}

diagnosis = s.diagnosis.diagnose(fake_report)
plan = s.repair_planner.plan(diagnosis)
approval = s.repair_approval.approve(plan)
execution = s.repair_execution_bridge.execute(approval)

print({
    "diagnosis": diagnosis,
    "plan": plan,
    "approval": approval,
    "execution": execution,
})
