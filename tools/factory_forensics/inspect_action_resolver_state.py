from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

resolver = r.improvement_action_resolver

print({
    "type": type(resolver).__name__,
    "methods": [
        x for x in dir(resolver)
        if not x.startswith("_")
    ],
    "dict": getattr(resolver, "__dict__", {})
})
