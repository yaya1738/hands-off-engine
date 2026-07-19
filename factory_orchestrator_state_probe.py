import json
import inspect

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator

o = FactoryDevelopmentOrchestrator()

print(json.dumps({
    "methods": {
        "create_development_task": str(inspect.signature(o.create_development_task)),
        "record_validation": str(inspect.signature(o.record_validation)),
        "history": str(inspect.signature(o.history)),
        "execute_task": str(inspect.signature(o.execute_task)),
    },
    "state": {
        k: v
        for k, v in o.__dict__.items()
    }
}, indent=2, default=str))
