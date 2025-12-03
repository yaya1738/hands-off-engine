import json
import sys
from pathlib import Path
from .command_executor import CommandExecutor
from .task_protocol import ExecutionTask

# Simple loader for config
def load_config():
    config_path = Path("config/executor_config.json")
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {} # Return safe defaults if missing

def run_agent_single_task(task_json):
    """
    Entry point for running a single task provided as a dict or JSON string.
    """
    config = load_config()
    executor = CommandExecutor(config)

    # Parse input
    if isinstance(task_json, str):
        data = json.loads(task_json)
    else:
        data = task_json

    # Hydrate Task
    task = ExecutionTask(
        task_id=data.get("task_id", "unknown"),
        command=data.get("command", []),
        working_dir=data.get("working_dir", "."),
        mode=data.get("mode", config.get("mode", "DRYRUN")),
        timeout_sec=data.get("timeout_sec", 60)
    )

    # Execute
    result = executor.execute(task)

    # Output
    print(json.dumps(result.to_json(), indent=2))

if __name__ == "__main__":
    # Basic CLI usage: python -m executor.autonomous_agent '{"command": ["ls"]}'
    if len(sys.argv) > 1:
        run_agent_single_task(sys.argv[1])
    else:
        print("Usage: python -m executor.autonomous_agent '<json_task_string>'")
