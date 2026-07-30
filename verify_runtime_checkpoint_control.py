from ai.factory.runtime import FactoryRuntime

try:
    r = FactoryRuntime()

    output = r.run_checkpoint_cycle()

    if output.get("state") in [
        "COMPLETE",
        "ERROR",
    ]:
        print({
            "status": "PASS",
            "goal": "RUNTIME_OWNS_CHECKPOINT_CONTROL",
            "output": output,
        })
    else:
        print({
            "status": "FAIL",
            "goal": "RUNTIME_OWNS_CHECKPOINT_CONTROL",
            "output": output,
        })

except Exception as e:
    print({
        "status": "ERROR",
        "goal": "RUNTIME_OWNS_CHECKPOINT_CONTROL",
        "error": str(e),
    })
