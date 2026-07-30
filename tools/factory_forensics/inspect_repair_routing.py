from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

for name in [
    "gap_repair_controller",
    "improvement_action_resolver",
    "development_translator",
    "development_advisor",
    "improvement_executor"
]:
    obj = getattr(r, name, None)

    print({
        "component": name,
        "type": type(obj).__name__ if obj else None,
        "methods": [
            x for x in dir(obj)
            if not x.startswith("_")
        ] if obj else []
    })
