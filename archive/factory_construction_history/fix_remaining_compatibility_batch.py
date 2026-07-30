from pathlib import Path

print({
    "status": "CREATE_COMPATIBILITY_REPAIR_BATCH",
    "targets": [
        "ai/factory/action_router.py",
        "ai/factory/decision_engine.py",
        "ai/factory/learning_memory.py",
        "ai/factory/feedback_engine.py",
    ],
})
