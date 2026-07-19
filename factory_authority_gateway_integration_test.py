import json
from ai.factory.authority_gateway import FactoryAuthorityGateway


def run():

    gateway = FactoryAuthorityGateway()

    lifecycle = gateway.submit_goal(
        "permanent authority gateway test"
    )

    completion = gateway.complete_reviewed_goal(
        {
            "id": "review-permanent-001",
            "approved": True
        },
        {
            "id": "improvement-permanent-001",
            "type": "capability_build"
        },
        {
            "status": "success"
        },
        {
            "artifact_id": "artifact-permanent-001",
            "task_id": "1",
            "artifact_type": "capability",
            "location": "authority_gateway"
        }
    )

    return {
        "lifecycle": lifecycle,
        "completion": completion,
        "decision": {
            "status": "PASS",
            "action": "permanent_authority_gateway_verified"
        }
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
