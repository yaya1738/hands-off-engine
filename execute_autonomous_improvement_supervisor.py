from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_SUPERVISOR",
    "reason": (
        "Factory requires a persistent internal loop that "
        "continuously detects capability gaps, creates "
        "improvement objectives, executes repairs, validates "
        "results, and learns without external intervention"
    )
}

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "success": result.get("success"),
    "steps_completed": result.get("steps_completed"),
    "learning_completed": (
        "learning" in result.get("steps_completed", [])
    )
})
