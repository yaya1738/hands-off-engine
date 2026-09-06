from __future__ import annotations

import json
from pathlib import Path

from ai.factory.autonomous_objective_loop import FactoryAutonomousObjectiveLoop
from ai.factory.runtime import FactoryRuntime


def main() -> int:
    runtime = FactoryRuntime()
    discovery = runtime.autonomy.discovery_gate(
        "discover the highest-value next autonomous objective",
        "scheduled autonomous objective cycle",
    )

    gaps = []
    capability_gap_analysis = discovery.get("capability_graph_analysis", {})
    if isinstance(capability_gap_analysis, dict):
        gaps.extend(capability_gap_analysis.get("gaps", []))

    selected = FactoryAutonomousObjectiveLoop(runtime).select_next(
        {
            "strategic_objective": "Continuously increase autonomous capability so routine operation requires progressively less human intervention, while continuously improve the system's ability to communicate dynamically, selectively, clearly, and powerfully with Yair when human input has genuine value.",
            "gaps": gaps,
            "discovery": discovery,
        }
    )

    result = {
        "schema": "autonomous-objective-cycle/v1",
        "discovery": discovery,
        "selection": selected,
        "execution": {
            "status": "not_started",
            "reason": "objective discovery is separated from authoritative execution",
            "authority": "FactoryAuthorityGateway",
        },
    }

    output = Path("autonomous-objective-cycle.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(selected, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
