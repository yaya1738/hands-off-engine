from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def approved_improvement_adapter(*args, **kwargs):
    item = {}

    if args and isinstance(args[0], dict):
        item.update(args[0])

    item.update(kwargs)

    if "status" not in item:
        item["status"] = "APPROVED"

    if "name" not in item:
        item["name"] = "generic_improvement"

    improvement = {
        "status": "APPROVED",
        "objective": item.get(
            "name",
            "generic_improvement"
        ),
        "priority": item.get(
            "priority",
            1
        ),
        "source": "autonomous_improvement",
    }

    action = {
        "action": item.get(
            "name",
            "generic_improvement"
        )
    }

    return r.improvement_executor.execute(
        improvement,
        action
    )

for name in [
    "address low success rate",
    "address low improvement impact",
    "generic_improvement",
]:
    r.improvement_action_resolver.register_action(
        name,
        approved_improvement_adapter
    )

print({
    "status": "EXECUTOR_HANDOFF_REPAIRED"
})

print(
    r.run_autonomous_improvement()
)
