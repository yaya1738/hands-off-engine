from ai.factory.runtime import FactoryRuntime

runtime = FactoryRuntime()

result = runtime.development_pipeline.process(
    {
        "objective": "artifact authority integration test",
        "context": {},
        "gaps": []
    }
)

print("PIPELINE STATUS:", result["status"])

print("PIPELINE REGISTRY COUNT:",
      len(runtime.development_pipeline.artifact_registry.list_artifacts()))

print("RUNTIME REGISTRY COUNT:",
      len(runtime.artifact_registry.list_artifacts()))

print("SAME OBJECT:",
      runtime.development_pipeline.artifact_registry is runtime.artifact_registry)
