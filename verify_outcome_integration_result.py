from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

audit = getattr(
    r.improvement_audit,
    "history",
    None
)

artifacts = getattr(
    r,
    "artifact_registry",
    None
)

factory_history = getattr(
    r,
    "_history",
    [])

print({
    "status": "ANALYZED",
    "checks": {
        "audit_history_exists": audit is not None,
        "artifact_registry_exists": artifacts is not None,
        "factory_history_exists": factory_history is not None,
    },
    "details": {
        "factory_history_count": len(factory_history),
        "artifact_type": (
            type(artifacts).__name__
            if artifacts else None
        ),
    },
    "next_action": (
        "VERIFY_PERSISTED_CHANGE"
        if len(factory_history) > 0
        else "TRACE_OUTCOME_STORAGE_PATH"
    )
})
