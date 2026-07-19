import json
import subprocess
from datetime import datetime, timezone


def probe():

    result = subprocess.run(
        ["python", "factory_construction_contract_probe.py"],
        capture_output=True,
        text=True
    )

    start = result.stdout.find("{")

    if start == -1:
        return {}

    return json.loads(result.stdout[start:])


def resolve(data):

    contracts = data.get("contracts", [])

    matches = []

    for item in contracts:
        name = item.get("class", "").lower()
        methods = item.get("methods", {})

        if (
            "artifact" in name
            or "verification" in name
            or "register" in str(methods).lower()
        ):
            matches.append(item)

    if matches:
        return {
            "decision": "registration_contract_found",
            "action": "build_thin_completion_adapter",
            "contracts": matches
        }

    return {
        "decision": "registration_contract_missing",
        "action": "extend_registration_capability"
    }


def run():

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_registration_contract_resolver",
        "decision": resolve(probe())
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
