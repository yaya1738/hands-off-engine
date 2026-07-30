from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

assessment = r.improvement_assessment

methods = [
    m for m in dir(assessment)
    if not m.startswith("_")
]

print({
    "status": "ANALYZED",
    "type": type(assessment).__name__,
    "methods": methods,
    "next_action": "IDENTIFY_ASSESSMENT_INPUTS"
})
