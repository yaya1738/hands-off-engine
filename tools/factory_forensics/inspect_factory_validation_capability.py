from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

checks = {
    "audit": hasattr(r, "improvement_audit"),
    "executor": hasattr(r, "improvement_executor"),
    "learning": hasattr(r, "learning"),
    "orchestrator": hasattr(r, "improvement_orchestrator"),
}

print({
    "status": "ANALYZED",
    "checks": checks,
    "next_action": (
        "CONNECT_VALIDATION_GATE"
        if all(checks.values())
        else "CREATE_MISSING_VALIDATION_CAPABILITY"
    )
})
