from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    before = len(
        r.learning.experiences
    )

    checkpoint = r.run_checkpoint_cycle()

    after = len(
        r.learning.experiences
    )

    print({
        "status": "PASS" if after > before else "FAIL",
        "checkpoint_action": checkpoint.get("action"),
        "learning_before": before,
        "learning_after": after,
        "next_action": (
            "CONTINUE"
            if after > before
            else "TRACE_RUNTIME_BRANCH"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVERY"
    })
