from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_FACTORY_SELF_IMPROVEMENT",
    "reason": "inspect"
}

submitted = r.submit_goal(goal)

print({
    "submitted_goal": submitted["goal"],
    "objective": submitted["goal"].get("objective"),
    "keys": list(submitted["goal"].keys()),
})
