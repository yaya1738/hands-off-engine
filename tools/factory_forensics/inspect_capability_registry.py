from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

registry = r.improvement_capability_registry

print({
    "type": type(registry).__name__,
    "methods": [
        x for x in dir(registry)
        if not x.startswith("_")
    ],
    "dict": getattr(registry, "__dict__", {})
})
