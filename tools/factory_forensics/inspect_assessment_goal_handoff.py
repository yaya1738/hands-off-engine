import inspect

from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

targets = [
    "improvement_assessment",
    "goal_manager",
    "goal_optimizer",
    "improvement_planner",
    "improvement_orchestrator",
]

result = {}

for name in targets:
    obj = getattr(r, name, None)
    if obj:
        methods = [
            m for m in dir(obj)
            if not m.startswith("_")
        ]
        result[name] = methods

print({
    "status": "ANALYZED",
    "handoff_components": result,
    "next_action": "TRACE_ASSESSMENT_TO_GOAL_FLOW"
})
