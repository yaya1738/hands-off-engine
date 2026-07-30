from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def generic_improvement_handler(task):
    return r.improvement_executor.execute(
        task,
        {
            "action": task.get("action", "generic_improvement")
        }
    )

actions = [
    "address low success rate",
    "address low improvement impact",
    "generic_improvement",
]

for action in actions:
    r.improvement_action_resolver.register_action(
        action,
        generic_improvement_handler
    )

print({
    "status": "BOOTSTRAPPED",
    "registered_actions": actions
})

result = r.run_autonomous_improvement()

print({
    "status": "AUTONOMOUS_RETRY",
    "result": result
})
