from ai.factory.runtime import FactoryRuntime
import inspect

try:
    r = FactoryRuntime()

    metrics = r.get_assessment_metrics()

    assessment = r.improvement_assessment.assess(
        metrics
    )

    planner_source = inspect.getsource(
        r.improvement_planner.plan
    )

    print({
        "status": "PASS" if (
            isinstance(assessment, dict)
            and "learning_experience_count" in metrics
            and "assessment" in planner_source
        ) else "FAIL",
        "checks": {
            "metrics_created": "learning_experience_count" in metrics,
            "assessment_returned": isinstance(assessment, dict),
            "planner_accepts_assessment": "assessment" in planner_source
        },
        "next_action": (
            "TRACE_IMPROVEMENT_DECISION"
            if isinstance(assessment, dict)
            else "REPAIR_ASSESSMENT_FLOW"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY"
    })
