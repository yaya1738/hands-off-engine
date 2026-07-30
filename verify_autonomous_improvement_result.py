from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "status": "ANALYZED",
    "learning_experiences": len(
        getattr(r.learning, "experiences", [])
    ),
    "audit_available": hasattr(
        r,
        "improvement_audit"
    ),
    "history_available": hasattr(
        r,
        "history"
    ),
    "next_action": "ASSESS_IMPROVEMENT_IMPACT"
})
