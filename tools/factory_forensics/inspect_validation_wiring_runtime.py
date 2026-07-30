from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

targets = [
    "execute_approved_improvement",
    "process_approved_improvement",
    "run_improvement_cycle",
    "trigger_improvement_pipeline",
]

results = {}

for name in targets:
    if hasattr(r, name):
        source = inspect.getsource(getattr(r, name))
        results[name] = {
            "mentions_validation": "validation" in source.lower(),
            "mentions_audit": "audit" in source.lower(),
            "mentions_registry": "registry" in source.lower(),
            "lines": len(source.splitlines()),
        }

print({
    "status": "ANALYZED",
    "runtime_validation_paths": results,
    "next_action": "CONNECT_IF_MISSING"
})
