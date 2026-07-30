from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

planner = r.improvement_planner

sig = inspect.signature(
    planner.prioritize
)

source = inspect.getsource(
    planner.prioritize
)

print({
    "status": "ANALYZED",
    "parameters": list(sig.parameters.keys()),
    "lines": len(source.splitlines()),
    "returns": [
        x.strip()
        for x in source.splitlines()
        if "return" in x
    ],
    "next_action": "DESIGN_BRIDGE"
})
