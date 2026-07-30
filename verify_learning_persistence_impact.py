from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

experiences = getattr(
    r.learning,
    "experiences",
    []
)

history = getattr(
    r.learning,
    "history",
    None
)

print({
    "status": "ANALYZED",
    "checks": {
        "learning_loaded": hasattr(r, "learning"),
        "experiences_available": len(experiences) > 0,
        "history_available": history is not None,
    },
    "details": {
        "experience_count": len(experiences),
    },
    "next_action": (
        "VERIFY_LEARNING_PERSISTENCE"
        if len(experiences) > 0
        else "CREATE_PERSISTENCE_REPAIR_PROPOSAL"
    )
})
