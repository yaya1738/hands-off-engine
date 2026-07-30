from ai.factory.runtime import FactoryRuntime
import inspect

try:
    source = inspect.getsource(
        FactoryRuntime.run_checkpoint_cycle
    )

    lines = source.splitlines()

    print({
        "method_found": True,
        "line_count": len(lines),
        "branches": [
            line.strip()
            for line in lines
            if "if " in line
            or "elif " in line
            or "else" in line
        ],
        "returns": [
            line.strip()
            for line in lines
            if "return" in line
        ],
        "contains": {
            "READY_TO_COMMIT": "READY_TO_COMMIT" in source,
            "REVIEW_REQUIRED": "REVIEW_REQUIRED" in source,
            "BLOCKED": "BLOCKED" in source,
        },
    })

except Exception as e:
    print({
        "method_found": False,
        "error": str(e),
    })
