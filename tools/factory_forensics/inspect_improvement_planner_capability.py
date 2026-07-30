from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

planner = r.improvement_planner

methods = [
    m for m in dir(planner)
    if not m.startswith("_")
]

print({
    "status": "ANALYZED",
    "planner_type": type(planner).__name__,
    "methods": methods,
    "next_action": "IDENTIFY_PRIORITY_METHOD"
})
