from ai.factory.runtime import FactoryRuntime
import json

r = FactoryRuntime()

result = {}

for name, obj in vars(r).items():
    result[name] = {
        "type": type(obj).__name__,
        "module": type(obj).__module__,
        "has_history": hasattr(obj, "history"),
        "has_execute": hasattr(obj, "execute"),
        "has_run": hasattr(obj, "run"),
        "has_record": hasattr(obj, "record"),
    }

print(json.dumps(result, indent=2, default=str))
