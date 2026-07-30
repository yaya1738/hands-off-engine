from ai.factory.runtime import FactoryRuntime

checks = {}
errors = []

try:
    r = FactoryRuntime()

    checks["runtime_loaded"] = True
    checks["checkpoint_manager_owned"] = hasattr(
        r,
        "checkpoint_manager",
    )
    checks["checkpoint_executor_owned"] = hasattr(
        r,
        "checkpoint_executor",
    )

    if checks["checkpoint_manager_owned"]:
        checks["manager_callable"] = callable(
            getattr(r.checkpoint_manager, "evaluate", None)
        )

    if checks["checkpoint_executor_owned"]:
        checks["executor_callable"] = callable(
            getattr(r.checkpoint_executor, "execute", None)
        )

except Exception as e:
    errors.append(str(e))

goal_met = (
    not errors
    and all(checks.values())
)

print(
    {
        "status": "PASS" if goal_met else "FAIL",
        "goal": "FACTORY_OWNS_CHECKPOINT_LIFECYCLE",
        "checks": checks,
        "errors": errors,
        "next_action": (
            "CONTINUE_INTEGRATION"
            if goal_met
            else "REPAIR_RUNTIME_WIRING"
        ),
    }
)
