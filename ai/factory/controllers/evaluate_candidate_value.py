from ai.factory.runtime import FactoryRuntime
from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence


CANDIDATES = [
    "adaptive_factory_improvement_step.py",
    "adaptive_validation_gap_controller.py",
    "checkpoint_flow_controller.py",
    "checkpoint_flow_decision.py",
    "checkpoint_learning_controller.py",
    "update_capability_graph.py",
    "update_gateway_capability.py",
]


def evaluate():

    runtime = FactoryRuntime()

    graph = FactoryCapabilityGraphIntelligence(
        runtime
    ).analyze()

    components = graph.get(
        "capability_graph",
        {}
    )

    results = []

    for candidate in CANDIDATES:

        words = candidate.replace(
            ".py",
            ""
        ).split("_")

        matches = []

        for component in components:

            score = sum(
                1
                for word in words
                if word in component.lower()
            )

            if score >= 2:
                matches.append(component)

        results.append(
            {
                "candidate": candidate,
                "existing_matches": matches,
                "decision": (
                    "REVIEW_FOR_UNIQUE_VALUE"
                    if not matches
                    else "DUPLICATE_OR_EXTENSION"
                ),
            }
        )

    return results


if __name__ == "__main__":
    for r in evaluate():
        print(r)
