import json
from pathlib import Path
from datetime import datetime, timezone


result = {
    "timestamp": datetime.now(timezone.utc).isoformat(),

    "decisions": [
        {
            "candidate": "adaptive_factory_improvement_step.py",
            "decision": "ARCHIVE_CANDIDATE",
            "reason": "decision helper duplicates adaptive_decision and improvement orchestration"
        },
        {
            "candidate": "checkpoint_learning_controller.py",
            "decision": "ARCHIVE_CANDIDATE",
            "reason": "no independent capability surface detected"
        },
        {
            "candidate": "checkpoint_flow_controller.py",
            "decision": "RESOLVED",
            "reason": "not present; capability exists through checkpoint_manager/executor"
        },
        {
            "candidate": "checkpoint_flow_decision.py",
            "decision": "RESOLVED",
            "reason": "decision capability already exists"
        },
        {
            "candidate": "update_capability_graph.py",
            "decision": "RESOLVED",
            "reason": "capability_graph_intelligence already active"
        },
        {
            "candidate": "update_gateway_capability.py",
            "decision": "RESOLVED",
            "reason": "gateway capability already integrated"
        }
    ]
}


Path(
    "state/candidate_resolution.json"
).write_text(
    json.dumps(result, indent=2)
)

print(result)
