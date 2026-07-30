from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

checks = {
    "history_available": hasattr(r, "history"),
    "audit_available": hasattr(r, "improvement_audit"),
    "artifact_registry": hasattr(r, "artifact_registry"),
    "development_pipeline": hasattr(r, "development_pipeline"),
    "improvement_orchestrator": hasattr(
        r,
        "improvement_orchestrator"
    ),
}

history = getattr(r, "_history", [])

print({
    "status": "ANALYZED",
    "checks": checks,
    "history_entries": len(history),
    "next_action": (
        "VERIFY_APPLIED_CHANGE"
        if len(history) > 0
        else "CONNECT_CHANGE_ARTIFACT_FLOW"
    )
})
