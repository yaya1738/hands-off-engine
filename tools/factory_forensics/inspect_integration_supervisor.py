from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "exists": hasattr(r, "integration_supervisor"),
    "type": type(r.integration_supervisor).__name__,
    "report": r.integration_supervisor.inspect(),
})
