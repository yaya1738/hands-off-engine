from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

matches = []

for name in dir(r):
    if "assessment" in name.lower():
        matches.append({
            "attribute": name,
            "type": type(getattr(r, name)).__name__
        })

components = [
    "improvement_orchestrator",
    "improvement_planner",
    "capability_assessment_runner",
    "factory_self_assessment",
]

for c in components:
    obj = getattr(r, c, None)
    if obj:
        methods = [
            m for m in dir(obj)
            if "assess" in m.lower()
        ]
        if methods:
            matches.append({
                "component": c,
                "assessment_methods": methods
            })

print({
    "status": "ANALYZED",
    "assessment_candidates": matches,
    "next_action": "TRACE_ASSESSMENT_SOURCE"
})
