import json
from datetime import datetime, timezone

def safe_import(path, name):
    try:
        module = __import__(path, fromlist=[name])
        return getattr(module, name)
    except Exception as e:
        return {
            "error": str(e),
            "missing": f"{path}.{name}"
        }


def run():
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_lifecycle_verifier",
        "checks": {}
    }

    # Existing construction organs
    DevelopmentOrchestrator = safe_import(
        "ai.factory.development_orchestrator",
        "FactoryDevelopmentOrchestrator"
    )

    DevelopmentExecutor = safe_import(
        "ai.factory.development_executor",
        "FactoryDevelopmentExecutor"
    )

    ArtifactRegistry = safe_import(
        "ai.factory.artifact_registry",
        "FactoryArtifactRegistry"
    )

    Runtime = safe_import(
        "ai.factory.runtime",
        "FactoryRuntime"
    )

    CompletionAdapter = safe_import(
        "factory_completion_wiring_adapter",
        "run"
    )

    result["checks"]["construction_orchestrator"] = (
        "available"
        if not isinstance(DevelopmentOrchestrator, dict)
        else DevelopmentOrchestrator
    )

    result["checks"]["development_executor"] = (
        "available"
        if not isinstance(DevelopmentExecutor, dict)
        else DevelopmentExecutor
    )

    result["checks"]["artifact_registry"] = (
        "available"
        if not isinstance(ArtifactRegistry, dict)
        else ArtifactRegistry
    )

    result["checks"]["runtime"] = (
        "available"
        if not isinstance(Runtime, dict)
        else Runtime
    )

    result["checks"]["completion_adapter"] = (
        "available"
        if not isinstance(CompletionAdapter, dict)
        else CompletionAdapter
    )

    available = [
        v == "available"
        for v in result["checks"].values()
    ]

    if all(available):
        result["decision"] = {
            "status": "PASS",
            "action": "lifecycle_components_connected"
        }
    else:
        result["decision"] = {
            "status": "INCOMPLETE",
            "action": "missing_lifecycle_component",
            "missing": [
                k for k,v in result["checks"].items()
                if v != "available"
            ]
        }

    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
