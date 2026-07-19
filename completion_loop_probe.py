from ai.factory.runtime import FactoryRuntime
import inspect

runtime = FactoryRuntime()

targets = [
    "execute_approved_improvement",
    "process_approved_improvement",
]

keywords = [
    "validation",
    "lifecycle",
    "artifact",
    "registry",
    "learning",
    "feedback",
    "record_outcome",
    "complete_change",
]

print("COMPLETION LOOP PROBE")
print("=" * 30)

for name in targets:
    print("\nMETHOD:", name)

    source = inspect.getsource(
        getattr(runtime, name)
    )

    for line in source.splitlines():
        if any(k in line.lower() for k in keywords):
            print(line.strip())

print("\nAVAILABLE RUNTIME COMPONENTS")
for name in [
    "development_pipeline",
    "learning_loop",
    "feedback_engine",
    "artifact_registry",
]:
    print(
        name,
        "=>",
        hasattr(runtime, name)
    )

print("DONE")
