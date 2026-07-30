from ai.factory.runtime import FactoryRuntime
import inspect

report = {
    "status": None,
    "checks": {},
    "next_action": None,
}

try:
    r = FactoryRuntime()

    planner = r.improvement_planner

    report["checks"]["planner_exists"] = True
    report["checks"]["prioritize_exists"] = callable(
        getattr(planner, "prioritize", None)
    )

    source = inspect.getsource(
        planner.prioritize
    )

    report["checks"]["uses_learning"] = (
        "learning" in source
        or "experience" in source
        or "history" in source
    )

    print({
        "status": "PASS" if all(report["checks"].values()) else "FAIL",
        "checks": report["checks"],
        "next_action": (
            "CONNECT_LEARNING_TO_PRIORITY"
            if not report["checks"]["uses_learning"]
            else "VERIFY_RUNTIME_FLOW"
        )
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
