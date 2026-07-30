from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def adaptive_improvement_handler(*args, **kwargs):
    task = {}

    if args:
        if isinstance(args[0], dict):
            task = args[0]

    if kwargs:
        task.update(kwargs)

    if not task:
        task = {
            "action": "generic_improvement",
            "source": "autonomous_improvement"
        }

    return r.improvement_executor.execute(
        task,
        {
            "action": task.get(
                "action",
                task.get(
                    "name",
                    "generic_improvement"
                )
            )
        }
    )

for name in [
    "address low success rate",
    "address low improvement impact",
    "generic_improvement",
]:
    r.improvement_action_resolver.register_action(
        name,
        adaptive_improvement_handler
    )

print({
    "status": "ACTION_SIGNATURE_REPAIRED"
})

print(
    r.run_autonomous_improvement()
)
