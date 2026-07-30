from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

checks = {
    "learning": hasattr(r, "learning"),
    "feedback": hasattr(r, "recommendation_feedback"),
    "audit": hasattr(r, "improvement_audit"),
    "event_bus": hasattr(r, "event_bus"),
    "emit_event": hasattr(r, "emit_event"),
}

print({
    "status": "ANALYZED",
    "feedback_capabilities": checks,
    "next_action": (
        "USE_EXISTING_FEEDBACK"
        if any(checks.values())
        else "CREATE_FEEDBACK_BRIDGE"
    )
})
