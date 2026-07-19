import json
import sys
from datetime import datetime, timezone


class FactoryCapabilityConfidenceGate:

    def __init__(self):
        self.history = []

    def evaluate(self, match_result):

        confidence = match_result.get("confidence", 0)

        if confidence >= 0.75:
            decision = "auto_reuse"

        elif confidence >= 0.40:
            decision = "review_existing_capability"

        else:
            decision = "build_new_capability"

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
            "decision": decision,
            "match": match_result.get("match", False),
            "capability": match_result.get("capability"),
        }

        self.history.append(result)

        return result


def run(match_result):
    return FactoryCapabilityConfidenceGate().evaluate(match_result)


if __name__ == "__main__":
    data = json.loads(" ".join(sys.argv[1:]))
    print(json.dumps(run(data), indent=2, default=str))
