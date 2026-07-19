import json
import inspect
from datetime import datetime, timezone

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.development_pipeline import FactoryDevelopmentPipeline
from ai.factory.development_executor import FactoryDevelopmentExecutor


def inspect_object(obj):

    data = {
        "class": obj.__class__.__name__,
        "methods": {}
    }

    for name in dir(obj):
        if any(x in name.lower() for x in [
            "create",
            "execute",
            "run",
            "validate",
            "report",
            "history"
        ]):
            try:
                data["methods"][name] = str(
                    inspect.signature(
                        getattr(obj, name)
                    )
                )
            except Exception:
                pass

    return data


def run():

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_contract_probe",
        "contracts": [
            inspect_object(FactoryDevelopmentOrchestrator()),
            inspect_object(FactoryDevelopmentPipeline()),
            inspect_object(FactoryDevelopmentExecutor())
        ]
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
