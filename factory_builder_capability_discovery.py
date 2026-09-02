"""Read-only compatibility facade for legacy capability discovery execution."""
import json

TOOLS = ["factory_forensic_engine.py", "factory_capability_analyzer.py"]


def run_tool(tool):
    return {
        "tool": tool,
        "success": False,
        "stdout": "",
        "stderr": "[FACTORY-AUTHORITY] direct tool execution is disabled; submit through FactoryAuthorityGateway",
        "authority_required": True,
    }


def run():
    return {
        "discovery": "factory_builder_capability_search",
        "tools": [],
        "authority": "FactoryAuthorityGateway",
        "disabled": True,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
