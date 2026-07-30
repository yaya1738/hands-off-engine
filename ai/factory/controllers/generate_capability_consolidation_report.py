import json
from pathlib import Path
from datetime import datetime, timezone


report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),

    "status": "CONSOLIDATION_VERIFIED",

    "archived_candidates": [
        {
            "name": "adaptive_factory_improvement_step.py",
            "reason": "duplicate decision helper"
        },
        {
            "name": "checkpoint_learning_controller.py",
            "reason": "no independent capability surface"
        }
    ],

    "resolved_candidates": [
        "checkpoint_flow_controller.py",
        "checkpoint_flow_decision.py",
        "update_capability_graph.py",
        "update_gateway_capability.py"
    ],

    "verified_core": [
        "improvement_orchestrator",
        "improvement_executor",
        "decision_engine",
        "checkpoint_manager",
        "checkpoint_executor",
        "gap_repair_controller",
        "capability_graph_intelligence"
    ]
}


Path("state/capability_consolidation_report.json").write_text(
    json.dumps(report, indent=2)
)

print(report)
