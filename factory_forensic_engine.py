from pathlib import Path
import json
import importlib.util


TOOLS = [
    "factory_artifact_registry",
    "factory_capability_analyzer",
    "factory_constructor_contract_analyzer",
    "factory_constructor_dependency_usage_audit",
    "factory_pipeline_usage_audit",
]


def load_tool(name):
    path = Path(name + ".py")

    if not path.exists():
        return {
            "tool": name,
            "loaded": False,
            "reason": "missing file",
        }

    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )

    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)

        return {
            "tool": name,
            "loaded": True,
            "exports": [
                x for x in dir(module)
                if not x.startswith("_")
            ],
        }

    except Exception as e:
        return {
            "tool": name,
            "loaded": False,
            "error": str(e),
        }


def discover():
    return {
        "engine": "factory_forensic_engine",
        "available_tools": [
            load_tool(tool)
            for tool in TOOLS
        ],
    }


if __name__ == "__main__":
    print(
        json.dumps(
            discover(),
            indent=2,
        )
    )
