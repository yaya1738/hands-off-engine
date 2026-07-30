from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

def adaptive_action(*args, **kwargs):
    return {
        "status": "ACTION_READY",
        "source": "adaptive_action_adapter",
    }

def resolver_adapter(*args, **kwargs):
    return adaptive_action

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
    "status": "RESOLVER_CONTRACT_ADAPTER_INSTALLED"
})

result = r.run_autonomous_improvement()

print({
    "status": "AUTONOMOUS_RETRY",
    "result": result
})
