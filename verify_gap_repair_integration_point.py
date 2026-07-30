from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

checks = {
    "runtime_loaded": True,
    "improvement_orchestrator": hasattr(
        r,
        "improvement_orchestrator"
    ),
    "improvement_assessment": hasattr(
        r,
        "improvement_assessment"
    ),
    "learning": hasattr(
        r,
        "learning"
    ),
}

print({
    "status": "READY" if all(checks.values()) else "MISSING",
    "checks": checks,
    "next_action": (
        "WIRE_GAP_CONTROLLER"
        if all(checks.values())
        else "REPAIR_FACTORY_ACCESS"
    )
})
