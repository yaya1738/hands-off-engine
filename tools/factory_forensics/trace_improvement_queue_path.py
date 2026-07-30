from ai.factory.runtime import FactoryRuntime
import inspect

try:
    r = FactoryRuntime()

    queue = r.improvement_orchestrator.queue

    methods = [
        m for m in dir(queue)
        if not m.startswith("_")
    ]

    candidates = {}

    for m in methods:
        try:
            source = inspect.getsource(
                getattr(queue, m)
            )

            refs = [
                x.strip()
                for x in source.splitlines()
                if (
                    "execute" in x.lower()
                    or "approve" in x.lower()
                    or "dispatch" in x.lower()
                    or "worker" in x.lower()
                )
            ]

            if refs:
                candidates[m] = refs

        except Exception:
            pass

    print({
        "status": "ANALYZED",
        "queue_type": type(queue).__name__,
        "methods": methods,
        "handoff_candidates": candidates,
        "next_action": "IDENTIFY_QUEUE_CONSUMER"
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
