from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

matches = []

for name in dir(r):
    if "metric" in name.lower():
        matches.append({
            "attribute": name,
            "type": type(getattr(r, name)).__name__
        })

for name in dir(r):
    obj = getattr(r, name)

    if callable(obj) and not name.startswith("_"):
        try:
            src = inspect.getsource(obj)
            if "assess(" in src and "metrics" in src:
                matches.append({
                    "method": name,
                    "contains": "assess(metrics)"
                })
        except Exception:
            pass

print({
    "status": "ANALYZED",
    "metric_candidates": matches,
    "next_action": "TRACE_METRIC_OWNER"
})
