"""
Integration Heartbeat

Single entry point for autonomous loops.
"""

from autonomous.integrations.supervisor import IntegrationSupervisor


def heartbeat():

    result = IntegrationSupervisor().run_once()

    failures = []

    for name, status in result["integrations"].items():

        if not status.get("connected", True):
            failures.append({
                "integration": name,
                "reason": "not_connected"
            })

        if "error" in status:
            failures.append({
                "integration": name,
                "reason": status["error"]
            })

    return {
        "healthy": len(failures) == 0,
        "failures": failures,
        "timestamp": result["timestamp"]
    }


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            heartbeat(),
            indent=2
        )
    )
