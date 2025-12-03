# Handoff System V2

**Version:** 2.0  
**Status:** Implemented  
**Last Updated:** 2025-12-03

## Overview

The improved handoff system provides robust task coordination between AI agents with validation, monitoring, recovery, and enforcement mechanisms.

## Key Improvements

### 1. Enhanced State Management

**Status States:**
- `pending` - Awaiting acceptance by target agent
- `accepted` - Agent acknowledged but hasn't started
- `in_progress` - Active work in progress
- `completed` - Successfully finished
- `failed` - Failed with error message
- `cancelled` - Cancelled by either party
- `timeout` - Exceeded timeout threshold

**Priority Levels:**
- `low` - Background tasks
- `normal` - Standard priority
- `high` - Important tasks
- `critical` - Urgent, immediate attention required

### 2. Validation & Capability Matching

**Task Validation:**
- Required fields: type, description
- Optional: files, requirements, estimated_duration, deliverables
- Structured validation before handoff creation

**Agent Capabilities:**
```python
copilot: code_review, pr_management, documentation, testing
claude-code: implementation, system_admin, debugging, refactoring
chatgpt: research, analysis, writing, planning
claude-web: research, analysis, planning, documentation
```

Handoffs are validated against target agent capabilities before creation.

### 3. Dependency Tracking

Handoffs can specify prerequisite handoffs that must complete first:

```python
manager.create_handoff(
    from_agent="claude-code",
    to_agent="copilot",
    task={
        "type": "code_review",
        "description": "Review trading module changes"
    },
    dependencies=["handoff-1234567890-claude-code-chatgpt"]  # Must complete first
)
```

### 4. Timeout Handling

**Default Timeout:** 60 minutes (configurable per handoff)

**Automatic Actions:**
- Self-healing agent checks for expired handoffs every 5 minutes
- Automatically marks expired handoffs as `timeout`
- Logs timeout events to history
- Alerts if timeout rate exceeds 10%

### 5. Retry Mechanism

**Failed Handoff Recovery:**
- Max retries: 3 (configurable)
- Automatic retry on failure (if enabled)
- Exponential backoff suggested for retry intervals
- Failed handoff permanently marked after max retries

### 6. Health Monitoring

**Metrics Tracked:**
- Total handoffs
- Completion rate
- Average duration
- Status distribution (pending, completed, failed, etc.)
- Per-agent statistics
- Priority distribution

**Thresholds:**
- Min completion rate: 70%
- Max failure rate: 15%
- Max timeout rate: 10%
- Max pending time: 120 minutes

**Automated Alerts:**
- Stale handoffs (pending > 2 hours)
- Low completion rate
- High failure rate
- High timeout rate
- Agent-specific high failure rates

### 7. Audit Trail

**Handoff History Log:** `ai/coordination/handoff_history.jsonl`

Every event is logged:
- Handoff creation
- Acceptance
- Start
- Completion
- Failure (with error)
- Cancellation
- Timeout

**Metrics File:** `ai/coordination/handoff_metrics.json`

Updated regularly with current health metrics.

## Usage

### Creating a Handoff

```python
from ai.coordination.handoff_manager import HandoffManager

manager = HandoffManager()

result = manager.create_handoff(
    from_agent="claude-code",
    to_agent="copilot",
    task={
        "type": "code_review",
        "description": "Review PR #123 - trading safeguards",
        "files": ["executor/trading_safeguards.py"],
        "requirements": ["code_review"],
        "estimated_duration": 30,
        "deliverables": ["review comments", "approval/changes requested"]
    },
    priority="high",
    context={
        "pr_url": "https://github.com/repo/pull/123",
        "urgency": "blocking deployment"
    },
    timeout_minutes=120
)

if result["success"]:
    print(f"Created handoff: {result['handoff_id']}")
else:
    print(f"Failed: {result['error']}")
```

### Accepting a Handoff

```python
result = manager.accept_handoff("handoff-1234567890", "copilot")

if result["success"]:
    # Start work
    manager.start_handoff("handoff-1234567890", "copilot")
```

### Completing a Handoff

```python
result = manager.complete_handoff(
    "handoff-1234567890",
    "copilot",
    result={
        "comments": ["LGTM, approved"],
        "status": "approved"
    }
)
```

### Handling Failures

```python
result = manager.fail_handoff(
    "handoff-1234567890",
    "copilot",
    error="Could not access repository",
    retry=True  # Will retry automatically
)
```

### Querying Handoffs

```python
# Get pending handoffs for an agent
pending = manager.get_pending_handoffs("copilot")

# Get all pending handoffs
all_pending = manager.get_pending_handoffs()

# Get metrics
metrics = manager.get_metrics()

# Check for timeouts
timed_out = manager.check_timeouts()
```

## CLI Interface

### Check Pending Handoffs

```bash
python3 ai/coordination/handoff_manager.py pending
python3 ai/coordination/handoff_manager.py pending copilot
```

### View Metrics

```bash
python3 ai/coordination/handoff_manager.py metrics
```

### Check for Timeouts

```bash
python3 ai/coordination/handoff_manager.py check-timeouts
```

### Run Health Check

```bash
python3 scripts/check_handoff_health.py
python3 scripts/check_handoff_health.py --json
```

## Integration with Self-Healing Agent

The handoff health check is integrated into the self-healing agent (`scripts/self_healing_agent.py`):

**Automatic Checks:**
- Runs every 5 minutes as part of health cycle
- Detects stale handoffs
- Marks timeouts
- Alerts on high failure rates
- Sends Telegram notifications for critical issues

**Manual Run:**
```bash
python3 scripts/self_healing_agent.py --once
```

## Integration with AI Nexus Hub

The enhanced handoff manager integrates with the existing AI Nexus Hub (`ai/integration/ai_nexus_hub.py`):

**Backward Compatibility:**
- Old `create_handoff()` method still works
- Automatically upgraded to V2 format
- Messages still sent via coordination channel

**Migration Path:**
```python
# Old way (still works)
hub.create_handoff(from_agent, to_agent, task, context)

# New way (recommended)
from ai.coordination.handoff_manager import HandoffManager
manager = HandoffManager()
manager.create_handoff(from_agent, to_agent, task, priority="high", timeout_minutes=90)
```

## File Structure

```
ai/coordination/
├── handoff_manager.py       # Enhanced handoff management
├── handoffs.json            # Handoff registry (V2 format)
├── handoff_history.jsonl    # Complete audit trail
├── handoff_metrics.json     # Current health metrics
└── messages.jsonl           # Inter-agent messages

scripts/
├── check_handoff_health.py  # Health monitoring script
└── self_healing_agent.py    # Includes handoff health check
```

## Data Structures

### Handoff V2 Format

```json
{
  "id": "handoff-1733235600-claude-code-copilot",
  "timestamp": "2025-12-03T13:00:00Z",
  "from_agent": "claude-code",
  "to_agent": "copilot",
  "task": {
    "type": "code_review",
    "description": "Review trading module",
    "files": ["executor/trading.py"],
    "requirements": ["code_review"],
    "estimated_duration": 30,
    "deliverables": ["review comments"]
  },
  "status": "in_progress",
  "priority": "high",
  "context": {
    "pr_url": "https://...",
    "urgency": "high"
  },
  "created_at": "2025-12-03T13:00:00Z",
  "accepted_at": "2025-12-03T13:05:00Z",
  "started_at": "2025-12-03T13:06:00Z",
  "completed_at": null,
  "failed_at": null,
  "dependencies": [],
  "timeout_minutes": 60,
  "retry_count": 0,
  "max_retries": 3,
  "error_message": null,
  "notes": [
    {
      "timestamp": "2025-12-03T13:05:00Z",
      "author": "copilot",
      "message": "Accepted by copilot"
    }
  ]
}
```

### Health Report Format

```json
{
  "timestamp": "2025-12-03T13:00:00Z",
  "status": "ok",
  "metrics": {
    "total_handoffs": 25,
    "completion_rate": 0.80,
    "average_duration_minutes": 45.2,
    "by_status": {
      "pending": 3,
      "in_progress": 2,
      "completed": 18,
      "failed": 1,
      "timeout": 1
    },
    "by_priority": {
      "low": 5,
      "normal": 15,
      "high": 4,
      "critical": 1
    },
    "by_agent": {
      "copilot": {
        "total": 12,
        "completed": 10,
        "failed": 0,
        "pending": 2
      }
    }
  },
  "alerts": [],
  "alert_count": 0
}
```

## Best Practices

### 1. Set Appropriate Timeouts

```python
# Quick tasks
timeout_minutes=30

# Normal tasks
timeout_minutes=60

# Complex tasks
timeout_minutes=120

# Research/long tasks
timeout_minutes=240
```

### 2. Use Priority Correctly

- `critical` - System down, deployment blocked, security issue
- `high` - Important feature, blocking other work
- `normal` - Standard work items
- `low` - Nice-to-have, background tasks

### 3. Specify Requirements

Always list required capabilities so validation can catch mismatches:

```python
task={
    "type": "research",
    "description": "Research market conditions",
    "requirements": ["research", "analysis"]  # Will match to chatgpt/claude-web
}
```

### 4. Add Context

Provide enough context for the target agent:

```python
context={
    "pr_url": "...",
    "branch": "feature/...",
    "related_issues": ["#123"],
    "urgency": "blocking",
    "background": "User requested..."
}
```

### 5. Track Dependencies

For multi-step workflows:

```python
# Step 1: Research
research_result = manager.create_handoff(
    from_agent="claude-code",
    to_agent="chatgpt",
    task={"type": "research", "description": "Research X"}
)

# Step 2: Implementation (depends on research)
impl_result = manager.create_handoff(
    from_agent="claude-code",
    to_agent="claude-code",
    task={"type": "implementation", "description": "Implement based on research"},
    dependencies=[research_result["handoff_id"]]
)

# Step 3: Review (depends on implementation)
review_result = manager.create_handoff(
    from_agent="claude-code",
    to_agent="copilot",
    task={"type": "code_review", "description": "Review implementation"},
    dependencies=[impl_result["handoff_id"]]
)
```

### 6. Monitor Health

Regular monitoring:

```bash
# Add to crontab
*/15 * * * * python3 /path/to/scripts/check_handoff_health.py --json >> /var/log/handoff-health.log
```

Or rely on self-healing agent (runs every 5 minutes automatically).

## Troubleshooting

### High Failure Rate

**Symptom:** Completion rate < 70% or failure rate > 15%

**Possible Causes:**
- Tasks assigned to wrong agents (capability mismatch)
- Unclear task descriptions
- Missing context/requirements
- Timeout too short

**Solutions:**
1. Review failed handoffs in history log
2. Check if tasks match agent capabilities
3. Add more context to handoffs
4. Increase timeouts for complex tasks

### Stale Handoffs

**Symptom:** Handoffs pending > 2 hours

**Possible Causes:**
- Target agent not actively monitoring
- Agent doesn't have capacity
- Unclear priority

**Solutions:**
1. Check if target agent is active
2. Consider reassigning to another agent
3. Mark critical handoffs with `priority="critical"`
4. Add notes to handoff explaining urgency

### Timeouts

**Symptom:** Timeout rate > 10%

**Possible Causes:**
- Timeout too short for task complexity
- Agent capacity issues
- Task blocked on external dependency

**Solutions:**
1. Increase default timeout
2. Set per-task timeouts based on estimated duration
3. Add dependencies to block until prerequisites complete
4. Check agent workload/capacity

## Migration from V1

The V1 handoff format is still supported but deprecated:

**V1 Format:**
```json
{
  "pending": [],
  "completed": [],
  "rejected": []
}
```

**V2 Format:**
```json
{
  "active": [],
  "completed": [],
  "protocol_version": "2.0"
}
```

**Automatic Migration:**
- V1 handoffs are automatically converted on first access
- No manual migration needed
- Backward compatible

## Future Enhancements

Planned improvements:

1. **Smart Routing:** AI-based agent selection based on task requirements
2. **Load Balancing:** Distribute tasks across agents based on capacity
3. **SLA Tracking:** Track and enforce service level agreements
4. **Escalation:** Auto-escalate stale handoffs to higher priority
5. **Templates:** Pre-defined handoff templates for common tasks
6. **Analytics:** Deeper insights into handoff patterns and bottlenecks

## References

- [AI Nexus Protocol](AI_NEXUS_PROTOCOL.md)
- [Development Standards](DEVELOPMENT_STANDARDS.md)
- [Fast Coordination System](../ai/coordination/FAST_COORDINATION_SYSTEM.md)

---

**For questions or issues, check the handoff history log or contact the coordination agent.**
