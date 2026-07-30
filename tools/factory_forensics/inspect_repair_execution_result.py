from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "executor": type(r.execution).__name__ if hasattr(r, "execution") else None,
    "improvement_executor": type(r.improvement_executor).__name__ if hasattr(r, "improvement_executor") else None,
    "development_pipeline": type(r.development_pipeline).__name__ if hasattr(r, "development_pipeline") else None,
    "components": [
        x for x in dir(r)
        if "repair" in x.lower()
        or "improve" in x.lower()
        or "develop" in x.lower()
    ]
})
