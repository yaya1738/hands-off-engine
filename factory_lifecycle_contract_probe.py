import json
import inspect
from datetime import datetime, timezone

from ai.factory.artifact_registry import FactoryArtifactRegistry
from ai.factory.verification_registry import FactoryVerificationRegistry


def inspect_obj(obj):
    result = {
        "class": obj.__class__.__name__,
        "methods": {}
    }

    for name in dir(obj):
        if any(x in name.lower() for x in [
            "register",
            "verify",
            "validation",
            "artifact",
            "find",
            "get",
            "list"
        ]):
            try:
                result["methods"][name] = str(
                    inspect.signature(getattr(obj,name))
                )
            except Exception:
                pass

    return result


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_lifecycle_contract_probe",
        "contracts": [
            inspect_obj(FactoryArtifactRegistry()),
            inspect_obj(FactoryVerificationRegistry())
        ]
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
