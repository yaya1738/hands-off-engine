import importlib
import inspect

targets = [
    "ai.factory.change_lifecycle_manager",
    "ai.factory.simulation_intelligence",
    "ai.factory.change_impact_analyzer",
    "ai.factory.validation_runner",
    "ai.factory.artifact_registry",
]

for module_name in targets:
    print("\n==============================")
    print(module_name)
    print("==============================")

    try:
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                print("\nCLASS:", name)

                methods = [
                    m for m in dir(obj)
                    if not m.startswith("_")
                    and callable(getattr(obj, m, None))
                ]

                print("METHODS:")
                for m in methods:
                    print(" -", m)

                source = inspect.getsource(obj)

                keywords = [
                    "artifact",
                    "generate",
                    "create",
                    "validate",
                    "simulate",
                    "impact",
                    "change",
                    "patch",
                    "file",
                    "write",
                    "execute",
                ]

                print("KEYWORD HITS:")
                for line in source.splitlines():
                    if any(k in line.lower() for k in keywords):
                        print(" ", line.strip())

    except Exception as e:
        print("ERROR:", e)
