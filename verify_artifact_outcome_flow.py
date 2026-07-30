from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

result = r.execute(
    {
        "task": "artifact_registry_test"
    }
)

artifacts = r.artifact_registry.list_artifacts()

print({
    "status": "ANALYZED",
    "execution_result": result.get("status") if isinstance(result, dict) else type(result).__name__,
    "artifact_count": len(artifacts),
    "artifacts": artifacts,
    "audit_available": hasattr(r, "improvement_audit"),
})
