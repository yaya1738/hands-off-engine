import json
import re
from difflib import SequenceMatcher


class FactoryCapabilityMatcher:

    def __init__(self, registry_file="factory_capability_registry_runtime.json"):
        self.registry_file = registry_file

    def normalize(self, text):
        return re.sub(
            r"[^a-z0-9 ]",
            "",
            text.lower()
        ).strip()

    def load_capabilities(self):
        capabilities = []

        try:
            with open(self.registry_file) as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        if item.get("validated"):
                            capabilities.append(item)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return capabilities

    def match(self, goal):

        goal_normalized = self.normalize(goal)

        best = None
        best_score = 0

        for capability in self.load_capabilities():

            name = self.normalize(
                capability.get("capability", "")
            )

            score = SequenceMatcher(
                None,
                goal_normalized,
                name
            ).ratio()

            if score > best_score:
                best_score = score
                best = capability

        return {
            "match": best_score >= 0.70,
            "confidence": round(best_score, 3),
            "capability": best,
        }


def run(goal):
    matcher = FactoryCapabilityMatcher()
    return matcher.match(goal)


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
