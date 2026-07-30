from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

print({
    "manager_type": type(r.checkpoint_manager).__name__,
    "manager_methods": [
        x for x in dir(r.checkpoint_manager)
        if not x.startswith("_")
    ],
    "executor_type": type(r.checkpoint_executor).__name__,
    "executor_methods": [
        x for x in dir(r.checkpoint_executor)
        if not x.startswith("_")
    ],
})
