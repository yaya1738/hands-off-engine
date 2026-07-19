import inspect
import json
from ai.factory.runtime import FactoryRuntime

OUTPUT = "factory_introspection_report.json"


def inspect_component(name, obj):
    result = {
        "type": type(obj).__name__,
        "methods": {}
    }

    for method_name in dir(obj):
        if method_name.startswith("_"):
            continue

        try:
            method = getattr(obj, method_name)

            if callable(method):
                result["methods"][method_name] = str(
                    inspect.signature(method)
                )
        except Exception:
            pass

    return result


print("FACTORY INTROSPECTION")
print("=" * 40)

factory = FactoryRuntime()

report = {
    "runtime_type": type(factory).__name__,
    "components": {}
}

for name, value in vars(factory).items():
    if name.startswith("_"):
        continue

    try:
        report["components"][name] = inspect_component(
            name,
            value
        )
        print(
            name,
            "=>",
            type(value).__name__
        )
    except Exception:
        pass


with open(OUTPUT, "w") as f:
    json.dump(
        report,
        f,
        indent=2
    )

print()
print("REPORT:", OUTPUT)
print("COMPONENT COUNT:", len(report["components"]))
print("DONE")
