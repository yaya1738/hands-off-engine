from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    metrics = r.get_assessment_metrics()

    assessment = r.improvement_assessment.assess(
        metrics
    )

    plan = r.improvement_planner.plan(
        assessment
    )

    priority = r.improvement_planner.prioritize(
        assessment
    )

    orchestrator = r.improvement_orchestrator

    methods = [
        m for m in dir(orchestrator)
        if not m.startswith("_")
    ]

    print({
        "status": "PASS" if (
            orchestrator is not None
            and len(methods) > 0
            and plan is not None
            and priority is not None
        ) else "FAIL",
        "checks": {
            "orchestrator_available": orchestrator is not None,
            "orchestrator_methods": len(methods) > 0,
            "plan_available": plan is not None,
            "priority_available": priority is not None
        },
        "next_action": (
            "TRACE_EXECUTION_HANDOFF"
            if orchestrator is not None
            else "CONNECT_ORCHESTRATOR"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY"
    })
