import json
from datetime import datetime, timezone

from ai.factory.runtime import FactoryRuntime


factory = FactoryRuntime()

result = factory.submit_development_request(
    "audit existing proposal handoff lifecycle",
    "transition probe"
)

report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "audit": "factory lifecycle transition probe",
    "result_keys": list(result.keys()) if isinstance(result, dict) else [],
    "result": result,
    "approval_history": factory.improvement_approval.history(),
    "executor_history": factory.improvement_executor.history(),
    "development_history": factory.development_tracker.history(),
}

with open(
    "factory_lifecycle_transition_probe.json",
    "w"
) as f:
    json.dump(
        report,
        f,
        indent=2,
        default=str
    )

print(json.dumps({
    "status": "complete",
    "output": "factory_lifecycle_transition_probe.json"
}, indent=2))
