import json
import inspect

from ai.factory.development_executor import FactoryDevelopmentExecutor

e = FactoryDevelopmentExecutor()

methods = [
    m for m in dir(e)
    if not m.startswith("_")
]

details = {}

for m in methods:
    try:
        details[m] = str(inspect.signature(getattr(e,m)))
    except:
        details[m] = "unknown"

print(json.dumps({
    "methods": details,
    "state": e.__dict__
}, indent=2, default=str))
