"""
Hands-Off Credential <-> Integration Bridge

Keeps lifecycle truth and connector reality aligned.
"""

import json
from datetime import datetime, timezone


def run():

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actions": [],
    }

    # Credential reality
    from autonomous.credentials.supervisor import CredentialSupervisor

    credentials = CredentialSupervisor().check_all()

    result["credentials"] = credentials


    # Integration reality
    from autonomous.integrations.heartbeat import heartbeat

    integration = heartbeat()

    result["integration"] = integration


    for item in credentials:

        identity = item["health"]["identity"]
        state = item["health"]["state"]

        connector = integration.get(
            "failures",
            []
        )

        gmail_failure = any(
            x.get("integration") == identity
            for x in connector
        )

        if state == "ACTIVE" and gmail_failure:
            result["actions"].append({
                "identity": identity,
                "action": "credential_connector_mismatch",
                "next": "reauthorization_required",
            })

        elif state == "VALIDATING" and gmail_failure:
            result["actions"].append({
                "identity": identity,
                "action": "awaiting_external_authorization",
            })

        else:
            result["actions"].append({
                "identity": identity,
                "action": "none",
            })


    return result


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2
        )
    )
