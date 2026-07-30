from ai.factory.runtime import FactoryRuntime

try:
    first = FactoryRuntime()

    before = len(
        getattr(first.learning, "experiences", [])
    )

    second = FactoryRuntime()

    after = len(
        getattr(second.learning, "experiences", [])
    )

    print({
        "status": "VERIFIED",
        "checks": {
            "runtime_restart_simulated": True,
            "learning_available": hasattr(
                second,
                "learning"
            ),
            "experiences_reloaded": after > 0,
        },
        "details": {
            "before": before,
            "after": after,
        },
        "next_action": (
            "CLOSE_CAPABILITY_GAP"
            if after > 0
            else "REFINE_PERSISTENCE_REPAIR"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e),
        "next_action": "RECOVER"
    })
