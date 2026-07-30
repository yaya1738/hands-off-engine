from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "action_router": type(r.action_router).__name__,
    "methods": [
        x for x in dir(r.action_router)
        if not x.startswith("_")
    ],
    "improvement_executor_history": r.improvement_executor.history(),
})
