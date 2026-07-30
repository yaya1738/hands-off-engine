from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

planner = r.improvement_planner

source = inspect.getsource(
    planner.plan
)

print({
    "status": "ANALYZED",
    "planner_plan_lines": len(source.splitlines()),
    "assessment_mentions": [
        x.strip()
        for x in source.splitlines()
        if "assessment" in x.lower()
    ],
    "returns": [
        x.strip()
        for x in source.splitlines()
        if "return" in x
    ],
    "next_action": "LOCATE_ASSESSMENT_OWNER"
})
