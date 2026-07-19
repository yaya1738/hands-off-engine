import json
import sys

from factory_capability_decision_pipeline import run as decide
from factory_capability_controller import FactoryCapabilityController


class FactoryCapabilityRoutingBridge:

    def __init__(self):
        self.controller = FactoryCapabilityController()

    def route(self, goal):

        decision = decide(goal)

        action = decision["decision"]["decision"]

        if action == "auto_reuse":
            result = self.controller.find_existing_capability(goal)

        elif action == "review_existing_capability":
            result = {
                "status": "review_required",
                "candidate": decision["decision"]["capability"]
            }

        else:
            result = self.controller.request_capability(goal)

        return {
            "goal": goal,
            "decision": decision["decision"],
            "action_result": result
        }


def run(goal):
    return FactoryCapabilityRoutingBridge().route(goal)


if __name__ == "__main__":

    goal = " ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
