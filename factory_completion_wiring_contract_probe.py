import json
import inspect
from datetime import datetime, timezone

TARGETS = [
    ("ai.factory.runtime", "FactoryDevelopmentTracker"),
    ("ai.factory.runtime", "FactoryImprovementApproval"),
    ("ai.factory.runtime", "FactoryImprovementQueue"),
    ("ai.factory.artifact_registry", "FactoryArtifactRegistry"),
]


def run():

    results = []

    for module_name, class_name in TARGETS:
        try:
            module = __import__(
                module_name,
                fromlist=[class_name]
            )

            cls = getattr(module, class_name)

            results.append({
                "class": class_name,
                "module": module_name,
                "constructor": str(
                    inspect.signature(cls)
                ),
                "methods": {
                    name: str(inspect.signature(getattr(cls, name)))
                    for name in dir(cls)
                    if not name.startswith("__")
                    and callable(getattr(cls, name))
                    and any(
                        x in name.lower()
                        for x in [
                            "approve",
                            "complete",
                            "verify",
                            "register"
                        ]
                    )
                }
            })

        except Exception as e:
            results.append({
                "class": class_name,
                "error": str(e)
            })

    return {
        "timestamp":
            datetime.now(timezone.utc).isoformat(),
        "component":
            "factory_completion_wiring_contract_probe",
        "contracts":
            results
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
