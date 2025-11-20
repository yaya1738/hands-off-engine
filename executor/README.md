# Executor Module

A safe, autonomous execution engine that provides a deterministic "body" for the AI "brain" to drive.

## Architecture

The executor implements a safety-first design:

- **Brain (AI/Planner)**: Generates commands and plans
- **Body (Executor)**: Executes commands with safety reflexes
- **Reflexes (SafetyAuditor)**: Rejects dangerous commands before execution

## Components

### 1. `task_protocol.py`
Defines the data structures for tasks and results:
- `ExecutionTask`: Input format for execution requests
- `ExecutionResult`: Output format with status, stdout, stderr

### 2. `safety_rules.py`
Safety auditor that performs static analysis:
- Command whitelist validation
- Blocked substring detection
- Path traversal prevention
- Workspace isolation

### 3. `command_executor.py`
The execution engine:
- DRYRUN mode: Simulates execution without running commands
- LIVE mode: Executes commands with timeout and error handling
- Safety checks before execution

### 4. `autonomous_agent.py`
CLI entry point for running tasks:
```bash
python -m executor.autonomous_agent '{"command": ["ls", "-la"], "mode": "DRYRUN"}'
```

## Configuration

Edit `config/executor_config.json` to customize:
- `mode`: Default execution mode ("DRYRUN" or "LIVE")
- `allowed_commands`: Whitelist of permitted commands
- `blocked_substrings`: Patterns that trigger rejection
- `protected_paths`: Paths that cannot be accessed
- `max_timeout_sec`: Maximum execution timeout

## Usage

### Python API

```python
from executor import CommandExecutor, ExecutionTask, load_config

# Load configuration
config = load_config()
executor = CommandExecutor(config)

# Create a task
task = ExecutionTask(
    task_id="my-task-001",
    command=["python", "script.py"],
    working_dir=".",
    mode="DRYRUN",
    timeout_sec=60
)

# Execute
result = executor.execute(task)

# Check result
if result.status == "success":
    print(result.stdout)
elif result.status == "rejected":
    print(f"Command rejected: {result.reason}")
```

### CLI

```bash
# Test in DRYRUN mode
python -m executor.autonomous_agent '{"command": ["ls"], "mode": "DRYRUN"}'

# Execute in LIVE mode (respects safety rules)
python -m executor.autonomous_agent '{"command": ["python", "test.py"], "mode": "LIVE"}'
```

## Safety Features

1. **Command Whitelist**: Only explicitly allowed commands can run
2. **Pattern Blocking**: Commands containing dangerous patterns are rejected
3. **Path Safety**: Commands cannot escape the workspace root
4. **Timeout Protection**: Commands are killed if they exceed timeout
5. **DRYRUN Mode**: Test commands without execution

## Testing

Run the test suite:
```bash
python tests/executor/test_basic_flow.py
```

Tests verify:
- DRYRUN mode simulation
- Rejection of unsafe commands
- Blocking of dangerous patterns
- Path traversal prevention
- JSON serialization

## Example: Safety in Action

```python
# Safe command - passes audit
task = ExecutionTask(
    task_id="safe",
    command=["python", "-c", "print('Hello')"]
)
# ✓ Executes successfully

# Unsafe command - rejected by safety rules
task = ExecutionTask(
    task_id="unsafe",
    command=["rm", "-rf", "/"]
)
# ✗ Rejected: "Command 'rm' is not whitelisted."

# Dangerous pattern - blocked
task = ExecutionTask(
    task_id="blocked",
    command=["echo", "sudo rm -rf /"]
)
# ✗ Rejected: "Command contains banned pattern: 'rm -rf'"
```

## Design Philosophy

The executor acts as a "reflex system" that protects against:
- AI hallucinations generating dangerous commands
- Accidental destructive operations
- Path traversal attacks
- Command injection attempts

By separating the deterministic executor (body) from the AI planner (brain), we create a safety layer that cannot be bypassed by prompt engineering or model errors.
