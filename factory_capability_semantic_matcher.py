import json
import re


class FactoryCapabilitySemanticMatcher:

    def __init__(self, registry_file="factory_capability_registry_runtime.json"):
        self.registry_file = registry_file

    def normalize_words(self, text):
        words = re.findall(
            r"[a-z0-9]+",
            text.lower()
        )

        synonyms = {
            "creator": "builder",
            "creating": "create",
            "created": "create",
            "software": "program",
            "application": "program",
            "generator": "builder",
            "maker": "builder",
            "develop": "build",
            "development": "build"
        }

        return set(
            synonyms.get(word, word)
            for word in words
        )

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
                        pass

        except FileNotFoundError:
            pass

        return capabilities

    def compare(self, goal, capability):

        goal_words = self.normalize_words(goal)

        capability_words = self.normalize_words(
            capability.get("capability", "")
        )

        if not goal_words:
            return 0

        overlap = (
            len(goal_words.intersection(capability_words))
            /
            len(goal_words.union(capability_words))
        )

        return round(overlap, 3)

    def match(self, goal):

        best = None
        best_score = 0

        for capability in self.load_capabilities():

            score = self.compare(
                goal,
                capability
            )

            if score > best_score:
                best_score = score
                best = capability

        return {
            "match": best_score >= 0.50,
            "confidence": best_score,
            "capability": best,
            "method": "semantic_keyword_match"
        }


def run(goal):
    return FactoryCapabilitySemanticMatcher().match(goal)


if __name__ == "__main__":
    import sys

    goal = " ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
