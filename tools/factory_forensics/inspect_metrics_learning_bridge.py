from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

method = r.get_assessment_metrics

source = inspect.getsource(method)

print({
    "status": "ANALYZED",
    "lines": len(source.splitlines()),
    "learning_reference": (
        "learning" in source.lower()
        or "experience" in source.lower()
    ),
    "history_reference": "history" in source.lower(),
    "returns": [
        x.strip()
        for x in source.splitlines()
        if "return" in x
    ],
    "next_action": (
        "VERIFY_METRIC_FLOW"
        if "learning" in source.lower()
        else "ADD_LEARNING_METRIC"
    )
})
