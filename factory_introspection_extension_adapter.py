import json
import importlib
import inspect
import pkgutil
from datetime import datetime, timezone


BASE_TOOL = "factory_constructor_contract_analyzer"


def load_existing_tool():
    try:
        return importlib.import_module(BASE_TOOL)
    except Exception as e:
        return {
            "load_error": str(e)
        }


def discover_modules(package_name="ai.factory"):
    modules = []

    try:
        package = importlib.import_module(package_name)

        for item in pkgutil.iter_modules(package.__path__):
            modules.append(item.name)

    except Exception:
        pass

    return modules


def inspect_object(obj):
    result = {
        "name": getattr(obj, "__name__", str(obj)),
        "functions": [],
        "classes": [],
    }

    try:
        for name, member in inspect.getmembers(obj):
            if inspect.isfunction(member):
                result["functions"].append({
                    "name": name,
                    "signature": str(
                        inspect.signature(member)
                    )
                })

            elif inspect.isclass(member):
                methods = []

                for method_name, method in inspect.getmembers(
                    member,
                    predicate=inspect.isfunction
                ):
                    methods.append({
                        "name": method_name,
                        "signature": str(
                            inspect.signature(method)
                        )
                    })

                result["classes"].append({
                    "name": name,
                    "methods": methods,
                })

    except Exception as e:
        result["error"] = str(e)

    return result


def run():

    existing = load_existing_tool()

    modules = discover_modules()

    inspected = []

    for module in modules:
        try:
            obj = importlib.import_module(
                f"ai.factory.{module}"
            )

            inspected.append(
                inspect_object(obj)
            )

        except Exception:
            continue


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_extension_adapter",
        "base_tool": BASE_TOOL,
        "extension_capabilities": {
            "module_discovery": True,
            "function_signature_inspection": True,
            "method_signature_inspection": True,
            "safe_dynamic_probe": True,
        },
        "existing_tool_loaded": not isinstance(
            existing,
            dict
        ),
        "modules_inspected": len(inspected),
        "sample": inspected[:3],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
