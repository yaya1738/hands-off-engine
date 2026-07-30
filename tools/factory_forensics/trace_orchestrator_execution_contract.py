from ai.factory.runtime import FactoryRuntime
import inspect

try:
    r = FactoryRuntime()

    o = r.improvement_orchestrator

    methods = [
        m for m in dir(o)
        if not m.startswith("_")
    ]

    candidates = {}

    for m in methods:
        try:
            source = inspect.getsource(
                getattr(o, m)
            )

            if (
                "plan" in source.lower()
                or "priority" in source.lower()
                or "execute" in source.lower()
            ):
                candidates[m] = [
                    x.strip()
                    for x in source.splitlines()
                    if (
                        "plan" in x.lower()
                        or "priority" in x.lower()
                        or "execute" in x.lower()
                    )
                ]
        except Exception:
            pass

    print({
        "status": "ANALYZED",
        "methods_checked": len(methods),
        "handoff_candidates": candidates,
        "next_action": "IDENTIFY_EXECUTION_OWNER"
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
