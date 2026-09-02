"""Read-only compatibility facade for legacy creator discovery.

The historical helper launched grep directly. Discovery and privileged creation
are now owned by FactoryAuthorityGateway.
"""

import json


SEARCH_TERMS = [
    "script creator",
    "code generator",
    "artifact creator",
    "development executor",
    "file generator",
    "builder",
]


def search_factory():
    return {
        "disabled": True,
        "error": "[FACTORY-AUTHORITY] legacy discovery execution is disabled; submit through FactoryAuthorityGateway",
        "search_terms": SEARCH_TERMS,
    }


def classify(results):
    if results.get("disabled"):
        return "factory_authority_required"
    text = json.dumps(results).lower()
    return "existing_script_creator_possible" if any(term in text for term in ("generate", "create_file", "artifact", "builder")) else "no_script_creator_found"


def run():
    discovery = search_factory()
    return {
        "component": "factory_script_creator_bootstrap",
        "discovery": discovery,
        "decision": classify(discovery),
        "next_action": "submit_creator_discovery_request",
        "authority": "FactoryAuthorityGateway",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
