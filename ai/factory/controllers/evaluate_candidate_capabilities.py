from ai.factory.runtime import FactoryRuntime
from ai.factory.capability_graph_intelligence import FactoryCapabilityGraphIntelligence
from pathlib import Path
import json


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

    graph_engine = FactoryCapabilityGraphIntelligence(
        runtime
    )

    graph_result = graph_engine.analyze()

    capability_graph = graph_result.get(
        "capability_graph",
        {}
    )

    detected_capabilities = list(
        capability_graph.keys()
    )

    results = []

    for candidate in CANDIDATES:

        name = candidate.replace(
            ".py",
            ""
        )

        related = [
            capability
            for capability in detected_capabilities
            if any(
                part in capability.lower()
                for part in name.split("_")
            )
        ]

        if related:
            status = "RELATED_EXISTING_CAPABILITY"
            reason = (
                "runtime already contains related capability"
            )
        else:
            status = "NEW_CAPABILITY_CANDIDATE"
            reason = (
                "no matching runtime capability detected"
            )

        results.append(
            {
                "candidate": candidate,
                "status": status,
                "reason": reason,
                "related_components": related,
            }
        )

    promote = [
        r["candidate"]
        for r in results
        if r["status"] == "NEW_CAPABILITY_CANDIDATE"
    ]

    hold = [
        r["candidate"]
        for r in results
        if r["status"] == "RELATED_EXISTING_CAPABILITY"
    ]

    return {
        "capability_count": graph_result.get(
            "component_count",
            0,
        ),
        "graph_status": graph_result.get(
            "status"
        ),
        "candidates": results,
        "factory_decision": {
            "investigate": promote,
            "hold": hold,
        },
    }


if __name__ == "__main__":

    result = evaluate()

    Path(
        "state/capability_candidate_evaluation.json"
    ).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    Path(
        "state/capability_candidate_evaluation.json"
    ).write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(result)
