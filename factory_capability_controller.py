import json
import sys
from datetime import datetime, timezone

from factory_capability_registry_bridge import run as build_and_register


class FactoryCapabilityController:

    def __init__(self):
        self.history = []

    def find_existing_capability(self, goal):
        try:
            with open("factory_capability_registry_runtime.json") as f:
                for line in f:
                    item = json.loads(line)
                    if item.get("capability") == goal and item.get("validated"):
                        return item
        except FileNotFoundError:
            pass

        return None

    def request_capability(self, goal):

        existing = self.find_existing_capability(goal)

        if existing:
            result = {
                "decision": "reuse_existing_capability",
                "capability": existing,
            }

        else:
            result = {
                "decision": "build_new_capability",
                "build": build_and_register(goal),
            }

        self.history.append(result)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goal": goal,
            "result": result,
        }


def run(goal):
    controller = FactoryCapabilityController()
    return controller.request_capability(goal)


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:])

    if not goal:
        goal = "create automatic program builder"

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
