# Approval System for Autonomous Agents

## Overview

The approval system manages changes that require user approval before execution.
All autonomous agents and Claude Code sessions should use this system for risky changes.

## When to Use Approval vs Auto-Apply

### Auto-Apply (Safe - No Approval Needed)
- Log file management (rotation, cleanup)
- Metrics collection and reporting
- Health checks and monitoring
- File permissions fixes
- Git lock cleanup
- Documentation updates
- Code comments
- Test additions
- Non-critical bug fixes

### Require Approval (Risky - User Must Approve)
- **Trading parameters** (position sizes, risk limits, thresholds)
- **Strategy/algorithm changes** (any logic affecting trading decisions)
- **Configuration changes** (API keys, endpoints, feature flags)
- **Cron schedule changes** (timing of operations)
- **System architecture** (adding/removing services, major refactors)
- **Critical code paths** (execution engine, order placement)
- **Dependency updates** (package.json, requirements.txt)
- **Database schema changes**

## How to Use (For Autonomous Agents)

```python
from ai.autonomous_change import propose_change

# Propose a change
result = propose_change(
    title="Increase max position size to $200",
    description="Alpha signals consistently showing 8%+ edge. Safe to increase position limits.",
    change_type="trading_parameters",  # Type determines auto-apply vs approval
    files=["config/risk_limits.json"],
    action={
        "type": "edit_file",
        "file_path": "/root/hands-off-engine/config/risk_limits.json",
        "old_content": '"max_position": 100',
        "new_content": '"max_position": 200'
    },
    risk_level="high"  # low, medium, high
)

if result["applied"]:
    print(f"Change auto-applied: {result['change_id']}")
else:
    print(f"Change pending approval: {result['change_id']}")
    # User will receive Telegram notification
    # They can approve with: /approve {change_id}
```

## Supported Action Types

### 1. Edit File
```python
{
    "type": "edit_file",
    "file_path": "/absolute/path/to/file",
    "old_content": "text to find",
    "new_content": "text to replace with"
}
```

### 2. Write File
```python
{
    "type": "write_file",
    "file_path": "/absolute/path/to/file",
    "content": "full file content"
}
```

### 3. Bash Command
```python
{
    "type": "bash_command",
    "command": "npm install new-package"
}
```

## User Workflow (Telegram)

When an approval is needed:

1. User receives Telegram notification:
   ```
   🔴 Approval Required

   Change #abc123
   Increase max position size to $200

   Type: trading_parameters
   Risk: high

   To approve: /approve abc123
   To reject: /reject abc123
   ```

2. User can:
   - `/pending` - See all pending approvals
   - `/approve abc123` - Execute the change
   - `/reject abc123 Too risky` - Reject with reason

3. System executes approved changes immediately

## Architecture

```
Autonomous Agent
       ↓
propose_change()
       ↓
   Risk Check
    ↙     ↘
Auto-Apply  Queue for Approval
    ↓            ↓
Execute    Send Telegram
    ↓            ↓
  Done    User Approves/Rejects
               ↓
           Execute/Cancel
```

## Files

- `ai/approval_queue.py` - Core queue management
- `ai/autonomous_change.py` - Simple API for agents
- `telegram/telegram_command_bot.py` - Telegram commands
- `state/approval_queue.json` - Queue state (pending/approved/rejected)

## For Claude Code Sessions

When you (Claude) want to make a risky change during an autonomous session:

1. Use `propose_change()` instead of directly editing files
2. System will either auto-apply or queue for approval
3. If queued, user gets Telegram notification
4. Document what you proposed in session notes
5. Don't wait for approval - move on to other tasks

## Examples

### Example 1: Trading Parameter Change (Needs Approval)
```python
propose_change(
    title="Reduce selection rate threshold to 40%",
    description="Current 50% threshold too conservative. 40% still maintains edge >6%.",
    change_type="trading_parameters",
    files=["config/alpha_config.json"],
    action={
        "type": "edit_file",
        "file_path": "/root/hands-off-engine/config/alpha_config.json",
        "old_content": '"min_selection_rate": 0.5',
        "new_content": '"min_selection_rate": 0.4'
    },
    risk_level="high"
)
```

### Example 2: Documentation Update (Auto-Applied)
```python
propose_change(
    title="Update README with new metrics",
    description="Added documentation for new performance metrics",
    change_type="documentation",
    files=["README.md"],
    action={
        "type": "edit_file",
        "file_path": "/root/hands-off-engine/README.md",
        "old_content": "## Metrics\n\nBasic metrics",
        "new_content": "## Metrics\n\nAdvanced metrics including edge and selection rate"
    },
    risk_level="low"
)
# This will auto-apply without approval
```

## Testing

Test the system:
```bash
# Test in CLI
python3 ai/autonomous_change.py

# Check queue
cat state/approval_queue.json

# Test Telegram commands
python3 -c "from telegram.telegram_command_bot import TelegramCommandBot; bot = TelegramCommandBot(); print(bot.process_command('/pending'))"
```
