from ai.factory.runtime import FactoryRuntime
import inspect

try:
    r = FactoryRuntime()

    source = inspect.getsource(
        r.improvement_orchestrator.run_cycle
    )

    print({
        "status": "ANALYZED",
        "lines": len(source.splitlines()),
        "execution_refs": [
            x.strip()
            for x in source.splitlines()
            if (
                "execute" in x.lower()
                or "queue" in x.lower()
                or "approve" in x.lower()
                or "dispatch" in x.lower()
            )
        ],
        "returns": [
            x.strip()
            for x in source.splitlines()
            if "return" in x
        ],
        "next_action": "MAP_EXECUTION_OWNER"
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
