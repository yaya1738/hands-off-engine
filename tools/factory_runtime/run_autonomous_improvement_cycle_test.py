from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    before = len(
        getattr(r.learning, "experiences", [])
    )

    result = r.run_improvement_cycle()

    after = len(
        getattr(r.learning, "experiences", [])
    )

    print({
        "status": "TESTED",
        "checks": {
            "cycle_returned": result is not None,
            "audit_available": hasattr(
                r,
                "improvement_audit"
            ),
            "learning_changed": after > before,
        },
        "details": {
            "learning_before": before,
            "learning_after": after,
            "result_type": type(result).__name__,
        },
        "next_action": (
            "VERIFY_AUTONOMOUS_REPAIR_PATH"
            if after > before
            else "CONNECT_IMPROVEMENT_FEEDBACK"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVER"
    })
