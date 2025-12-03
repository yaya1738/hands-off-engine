# AI Coordination Directory

This directory contains files for coordinating work between AI agents (Copilot, Claude-Code, ChatGPT, Claude-Web).

## Files

### Core Coordination Files

**handoffs.json** - Central registry of task handoffs between agents
- Format: V2 (enhanced with validation and monitoring)
- Contains: active handoffs, completed handoffs, protocol version
- Updated by: `handoff_manager.py`

**messages.jsonl** - Inter-agent message log
- Format: JSON Lines (one message per line)
- Contains: all agent-to-agent messages
- Used for: coordination, notifications, broadcasts

**status.json** - Overall coordination status
- Contains: active agents, current phase, pending tasks
- Updated by: coordination agent
- Read by: all agents for status awareness

### Handoff System V2 Files

**handoff_manager.py** - Enhanced handoff management system
- Executable: `python3 handoff_manager.py <command>`
- Commands: `pending [agent]`, `metrics`, `check-timeouts`
- Features: validation, retry logic, timeout detection, health monitoring

**handoff_history.jsonl** - Complete audit trail of handoff events
- Format: JSON Lines
- Events: created, accepted, started, completed, failed, cancelled, timeout
- Used for: debugging, analysis, compliance

**handoff_metrics.json** - Current handoff health metrics
- Updated by: `handoff_manager.py` when metrics requested
- Contains: completion rate, failure rate, timeout rate, per-agent stats
- Used for: health monitoring, alerting

### Other Files

**copilot_tasks.jsonl** - Task assignments for Copilot agent
- Format: JSON Lines
- Contains: assigned tasks, status, timestamps

**active_directive.json** - Current coordination directive
- Contains: priority guidance for all agents

## Usage

### Create a Handoff

```python
from ai.coordination.handoff_manager import HandoffManager

manager = HandoffManager()

result = manager.create_handoff(
    from_agent="claude-code",
    to_agent="copilot",
    task={
        "type": "code_review",
        "description": "Review PR #123",
        "requirements": ["code_review"],
        "files": ["file.py"]
    },
    priority="high",
    timeout_minutes=120
)
```

### Query Handoffs

```bash
# List pending handoffs
python3 handoff_manager.py pending

# List pending for specific agent
python3 handoff_manager.py pending copilot

# Get metrics
python3 handoff_manager.py metrics

# Check for timeouts
python3 handoff_manager.py check-timeouts
```

### Monitor Health

```bash
# Run health check
python3 ../../scripts/check_handoff_health.py

# Get JSON output
python3 ../../scripts/check_handoff_health.py --json
```

## Health Monitoring

The handoff system is monitored by the self-healing agent (`scripts/self_healing_agent.py`):

**Check Interval:** Every 5 minutes

**Thresholds:**
- Min completion rate: 70%
- Max failure rate: 15%
- Max timeout rate: 10%
- Max pending time: 120 minutes

**Actions:**
- Automatically marks expired handoffs as timeout
- Alerts on unhealthy metrics
- Logs issues for investigation

## Agent Capabilities

When creating handoffs, tasks are validated against agent capabilities:

| Agent | Capabilities |
|-------|-------------|
| copilot | code_review, pr_management, documentation, testing |
| claude-code | implementation, system_admin, debugging, refactoring |
| chatgpt | research, analysis, writing, planning |
| claude-web | research, analysis, planning, documentation |

## Documentation

**Full Documentation:** [docs/HANDOFF_SYSTEM_V2.md](../../docs/HANDOFF_SYSTEM_V2.md)

Covers:
- Complete API reference
- Usage examples
- Best practices
- Troubleshooting
- Migration from V1

## Testing

Run tests:
```bash
python3 ../../tests/test_handoff_system.py
```

Tests cover:
- Handoff creation and validation
- State transitions
- Timeout detection
- Retry logic
- Metrics calculation
- Agent capability matching
- Dependency resolution

## Protocol Version

**Current:** 2.0

**Changes from V1:**
- Enhanced state management (7 statuses vs 3)
- Priority levels
- Timeout handling
- Retry mechanism
- Agent capability matching
- Dependency tracking
- Health monitoring

V1 handoffs are automatically upgraded to V2 format on first access.

## For More Information

See:
- [Handoff System V2 Documentation](../../docs/HANDOFF_SYSTEM_V2.md)
- [AI Nexus Protocol](../integration/AI_NEXUS_PROTOCOL.md)
- [Fast Coordination System](FAST_COORDINATION_SYSTEM.md)
