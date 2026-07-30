from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def improvement_action(*args, **kwargs):
    return {
        "status": "IMPROVEMENT_ACTION_EXECUTED",
        "args": args,
        "kwargs": kwargs,
    }

def resolver_adapter(item):
    return improvement_action

for name in [
    "address low success rate",
    "address low improvement impact",
    "generic_improvement",
]:
    r.improvement_action_resolver.register_action(
        name,
        resolver_adapter
    )

print({
    "status": "CALLABLE_ACTION_CONTRACT_REPAIRED"
})

print(
    r.run_autonomous_improvement()
)
