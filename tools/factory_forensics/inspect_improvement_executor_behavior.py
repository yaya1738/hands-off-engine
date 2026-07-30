from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

executor = r.improvement_executor

print({
    "executor_type": type(executor).__name__,
    "methods": [
        x for x in dir(executor)
        if not x.startswith("_")
    ],
    "history": executor.history()
})
