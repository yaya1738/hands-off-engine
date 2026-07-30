from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    before = len(
        r.learning.experiences
    )

    r.run_checkpoint_cycle()

    after = len(
        r.learning.experiences
    )

    metrics = r.get_assessment_metrics()

    print({
        "status": "PASS" if (
            after > before
            and "learning_experience_count" in metrics
            and metrics["learning_experience_count"] == after
        ) else "FAIL",
        "checks": {
            "learning_created": after > before,
            "metric_exists": "learning_experience_count" in metrics,
            "metric_matches_learning": (
                metrics.get("learning_experience_count") == after
            )
        },
        "next_action": (
            "CONTINUE_INTEGRATION"
            if (
                after > before
                and metrics.get("learning_experience_count") == after
            )
            else "TRACE_METRIC_FLOW"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY"
    })
