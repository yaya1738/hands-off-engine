import json
from datetime import datetime, timezone

from ai.factory.runtime import FactoryRuntime


def safe_history(obj, name):
    try:
        value = getattr(obj, name)()
        return value
    except Exception as e:
        return {
            "error": str(e)
        }


factory = FactoryRuntime()

report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "audit": "factory bridge usage audit",
    "checks": {}
}


# Component existence
report["checks"]["components"] = {
    "approval": hasattr(factory, "improvement_approval"),
    "executor": hasattr(factory, "improvement_executor"),
    "tracker": hasattr(factory, "development_tracker"),
    "planner": hasattr(factory, "improvement_planner"),
}


# Existing histories
report["checks"]["histories"] = {
    "approval_history": safe_history(
        factory.improvement_approval,
        "history"
    ),
    "executor_history": safe_history(
        factory.improvement_executor,
        "history"
    ),
    "development_history": safe_history(
        factory.development_tracker,
        "history"
    ),
}


# Look for existing bridge artifacts
approval_history = report["checks"]["histories"]["approval_history"]
executor_history = report["checks"]["histories"]["executor_history"]
development_history = report["checks"]["histories"]["development_history"]


report["checks"]["bridge_state"] = {
    "verified_tasks_exist": any(
        isinstance(x, dict)
        and x.get("status") == "verified"
        for x in development_history
    ) if isinstance(development_history, list) else False,

    "approval_requests_exist": isinstance(
        approval_history,
        list
    ) and len(approval_history) > 0,

    "executor_runs_exist": isinstance(
        executor_history,
        list
    ) and len(executor_history) > 0,
}


report["conclusion"] = {
    "verified_task_to_approval":
        "PRESENT" if report["checks"]["bridge_state"]["approval_requests_exist"]
        else "MISSING_OR_UNUSED",

    "approval_to_executor":
        "PRESENT" if report["checks"]["bridge_state"]["executor_runs_exist"]
        else "MISSING_OR_UNUSED",
}


with open(
    "factory_bridge_usage_audit.json",
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
    "output": "factory_bridge_usage_audit.json"
}, indent=2))
