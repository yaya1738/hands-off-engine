import json
from factory_capability_semantic_matcher import FactoryCapabilitySemanticMatcher
from factory_capability_controller import FactoryCapabilityController


class FactoryCapabilityDecisionAdapter:

    def __init__(self):
        self.matcher = FactoryCapabilitySemanticMatcher()
        self.controller = FactoryCapabilityController()

    def decide(self, goal):

        semantic = self.matcher.match(goal)

        if semantic["match"]:
            return {
                "decision": "reuse_existing_capability",
                "reason": "semantic_match",
                "confidence": semantic["confidence"],
                "capability": semantic["capability"],
            }

        return {
            "decision": "build_new_capability",
            "reason": "no_sufficient_match",
            "confidence": semantic["confidence"],
            "capability": None,
        }


def run(goal):
    return FactoryCapabilityDecisionAdapter().decide(goal)


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
