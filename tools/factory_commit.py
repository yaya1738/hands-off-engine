"""Read-only compatibility facade for legacy repository commit helper.

Repository mutation is an authority operation and must be performed through
the FactoryAuthorityGateway rather than a local shell command.
"""

import json


def run(cmd):
    return {
        "disabled": True,
        "error": "[FACTORY-AUTHORITY] legacy git execution is disabled; submit through FactoryAuthorityGateway",
        "command": list(cmd),
    }


def main():
    return {
        "component": "factory_commit",
        "disabled": True,
        "decision": "factory_authority_required",
        "next_step": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
