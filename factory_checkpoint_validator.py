from pathlib import Path
import json
import sys


CHECKPOINT = Path("factory_runtime_checkpoint.json")


REQUIRED_FIELDS = [
    "timestamp",
    "checkpoint",
    "runtime_state",
    "validated_capabilities",
    "health_status",
    "next_phase",
]


REQUIRED_CAPABILITIES = [
    "factory_report",
    "integrity_report",
    "maintenance_status",
    "operator_status",
    "trend_report",
    "history",
]


def validate():
    results = {
        "checkpoint_exists": CHECKPOINT.exists(),
        "checks": [],
        "healthy": False,
    }

    if not CHECKPOINT.exists():
        results["checks"].append(
            {
                "check": "checkpoint_file",
                "passed": False,
                "reason": "missing file",
            }
        )
        return results

    data = json.loads(
        CHECKPOINT.read_text()
    )

    for field in REQUIRED_FIELDS:
        results["checks"].append(
            {
                "check": f"field:{field}",
                "passed": field in data,
            }
        )

    capabilities = data.get(
        "validated_capabilities",
        [],
    )

    for capability in REQUIRED_CAPABILITIES:
        results["checks"].append(
            {
                "check": f"capability:{capability}",
                "passed": capability in capabilities,
            }
        )

    results["checks"].append(
        {
            "check": "factory_health",
            "passed": (
                data.get("health_status", {})
                .get("factory_health")
                == "healthy"
            ),
        }
    )

    results["checks"].append(
        {
            "check": "contracts",
            "passed": (
                data.get("health_status", {})
                .get("contracts")
                == "passing"
            ),
        }
    )

    results["healthy"] = all(
        item["passed"]
        for item in results["checks"]
    )

    return results


def main():
    result = validate()

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    if not result["healthy"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
