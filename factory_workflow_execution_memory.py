from pathlib import Path
import json
from datetime import datetime, timezone
import sys


MEMORY = Path("factory_workflow_execution_memory.json")


def load_memory():
    if MEMORY.exists():
        return json.loads(MEMORY.read_text())

    return {
        "executions": []
    }


def save_memory(data):
    MEMORY.write_text(
        json.dumps(
            data,
            indent=2,
        )
    )


def record_execution(
    workflow,
    status,
    details=None,
):
    memory = load_memory()

    entry = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "workflow": workflow,
        "status": status,
        "details": details or {},
    }

    memory["executions"].append(entry)

    save_memory(memory)

    return entry


def history():
    return load_memory()


def main():

    if len(sys.argv) < 3:
        print(
            "Usage: python factory_workflow_execution_memory.py <workflow> <status>"
        )
        sys.exit(1)

    result = record_execution(
        workflow=sys.argv[1],
        status=sys.argv[2],
        details={
            "source": "factory_workflow_executor"
        },
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
