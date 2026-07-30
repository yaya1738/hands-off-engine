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

    print({
        "status": "PASS" if (
            isinstance(plan, dict)
            and priority is not None
        ) else "FAIL",
        "checks": {
            "assessment_exists": isinstance(assessment, dict),
            "plan_created": isinstance(plan, dict),
            "priority_created": priority is not None
        },
        "next_action": (
            "VERIFY_ORCHESTRATOR_HANDOFF"
            if isinstance(plan, dict)
            else "REPAIR_PLANNER_FLOW"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY"
    })
