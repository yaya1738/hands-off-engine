import json
import sys
from factory_capability_semantic_matcher import FactoryCapabilitySemanticMatcher
from factory_capability_confidence_gate import FactoryCapabilityConfidenceGate
from datetime import datetime, timezone


def run(goal):

    matcher = FactoryCapabilitySemanticMatcher()
    gate = FactoryCapabilityConfidenceGate()

    match_result = matcher.match(goal)
    decision = gate.evaluate(match_result)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "matcher": match_result,
        "decision": decision
    }


if __name__ == "__main__":

    goal = " ".join(sys.argv[1:])

    print(json.dumps(
        run(goal),
        indent=2,
        default=str
    ))
