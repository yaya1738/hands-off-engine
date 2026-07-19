import json
from datetime import datetime, timezone

from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryIntegrationResolver:

    def __init__(self):
        self.gateway = FactoryAuthorityGateway()

    def resolve(self, capability):

        report = self.gateway.report()

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": "factory_integration_resolver",
            "capability": capability,
            "available": {
                "authority_gateway": True,
                "construction": "construction" in report.get("lifecycle", {}),
                "completion": "completion" in report.get("lifecycle", {})
            },
            "decision": None
        }

        missing = []

        for name, available in result["available"].items():
            if not available:
                missing.append(name)

        if not missing:
            result["decision"] = {
                "action": "wire_existing_components",
                "status": "ready"
            }
        else:
            result["decision"] = {
                "action": "request_construction",
                "status": "missing_components",
                "missing": missing
            }

        return result


def run():
    resolver = FactoryIntegrationResolver()

    return resolver.resolve(
        "autonomous authority lifecycle execution"
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
