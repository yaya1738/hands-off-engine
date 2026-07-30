from ai.factory.runtime import FactoryRuntime
import inspect

try:
    source = inspect.getsource(
        FactoryRuntime.run_checkpoint_cycle
    )

    print({
        "status": "ANALYZED",
        "lines": len(source.splitlines()),
        "returns": [
            x.strip()
            for x in source.splitlines()
            if "return" in x
        ],
        "checkpoint_calls": [
            x.strip()
            for x in source.splitlines()
            if "checkpoint" in x.lower()
        ][-10:]
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
