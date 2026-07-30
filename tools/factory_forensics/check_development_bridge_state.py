from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.run_autonomous_improvement()

print({
    "development_present": result.get("development") is not None,
    "development_type": type(result.get("development")).__name__,
    "development": result.get("development"),
})
