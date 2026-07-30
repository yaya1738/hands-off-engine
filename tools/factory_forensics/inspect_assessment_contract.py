from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

method = r.improvement_assessment.assess

sig = inspect.signature(method)

source = inspect.getsource(method)

print({
    "status": "ANALYZED",
    "parameters": list(sig.parameters.keys()),
    "lines": len(source.splitlines()),
    "references": [
        x.strip()
        for x in source.splitlines()
        if "history" in x.lower()
        or "learning" in x.lower()
        or "experience" in x.lower()
        or "gap" in x.lower()
    ],
    "next_action": "DESIGN_ASSESSMENT_BRIDGE"
})
