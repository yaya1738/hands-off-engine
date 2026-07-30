from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "resolver_actions": getattr(
        r.improvement_action_resolver,
        "_actions",
        None
    ),
    "executor_methods": [
        x for x in dir(r.improvement_executor)
        if not x.startswith("_")
    ],
    "resolver_source": r.improvement_action_resolver.resolve.__code__.co_filename,
})

for name in [
    "address low success rate",
    "address low improvement impact",
    "generic_improvement",
]:
    print(
        name,
        r.improvement_action_resolver.resolve(
            {"action": name}
        )
    )
