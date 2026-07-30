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

result = r.submit_goal(goal)

print({
    "status": "SUBMITTED",
    "result": result
})
