# Telegram Bot Integration with Copilot Tasks

## Overview

The Telegram bot (`@pm_alerts_autobot`) integrates with the Copilot Tasks system to allow creating and tracking tasks via Telegram.

## Commands for Task Management

### Creating Tasks

**Create a Copilot task:**
```
/task <description>
```

This queues a task that will be picked up by the autonomous agents. For GitHub Copilot to specifically handle it, the task will be created as a GitHub issue with the `copilot-task` label.

**Examples:**
```
/task Add endpoint to fetch alpha signals
/task Fix bug in position sizing calculation
/task Update documentation for risk model
```

### Checking Task Status

**List open Copilot tasks:**
```
/tasks
```

Shows all currently open tasks assigned to Copilot agent, including:
- Issue number
- Title
- Status (assigned, in_progress, completed)
- Time elapsed

**Get status of specific task:**
```
/task-status <id>
```

Shows detailed status of a specific task including:
- Current status
- Branch name (if in progress)
- PR number (if completed)
- Time since assignment

**Examples:**
```
/tasks
/task-status 42
```

### GitHub Spark Integration

**Link to Spark apps:**
```
/spark <app-name>
```

Returns a link to the specified Spark app:
- `trading` - Trading dashboard
- `agents` - Agent monitor
- `risk` - Risk control panel

**Example:**
```
/spark trading
→ Returns: https://github.com/spark/yaya1738-hands-off-trading-dashboard
```

## Implementation Notes

These commands should be added to `telegram/telegram_command_bot.py`:

### /tasks command
```python
def cmd_tasks(self, args) -> str:
    """List open Copilot tasks."""
    tasks_file = AI_COORD_DIR / "copilot_tasks.jsonl"
    if not tasks_file.exists():
        return "📋 No Copilot tasks found"
    
    tasks = []
    with open(tasks_file) as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                if task.get('status') != 'merged':
                    tasks.append(task)
    
    if not tasks:
        return "✅ No open Copilot tasks"
    
    response = "📋 **Open Copilot Tasks**\n\n"
    for task in tasks[-10:]:  # Last 10 tasks
        issue = task.get('issue', 'N/A')
        status = task.get('status', 'unknown')
        title = task.get('title', 'Untitled')
        response += f"#{issue} - {status}\n{title}\n\n"
    
    return response
```

### /task-status command
```python
def cmd_task_status(self, args) -> str:
    """Get status of specific Copilot task."""
    if not args:
        return "❌ Usage: /task-status <issue-number>"
    
    try:
        issue_num = int(args[0])
    except ValueError:
        return "❌ Invalid issue number"
    
    tasks_file = AI_COORD_DIR / "copilot_tasks.jsonl"
    if not tasks_file.exists():
        return f"❌ Task #{issue_num} not found"
    
    # Find task in log
    task_data = None
    with open(tasks_file) as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                if task.get('issue') == issue_num:
                    task_data = task
    
    if not task_data:
        return f"❌ Task #{issue_num} not found"
    
    # Format response
    status = task_data.get('status', 'unknown')
    branch = task_data.get('branch', 'N/A')
    pr = task_data.get('pr', 'N/A')
    timestamp = task_data.get('timestamp', 'N/A')
    
    response = f"""📊 **Task #{issue_num} Status**

Status: {status}
Branch: {branch}
PR: {pr}
Last Updated: {timestamp}
"""
    return response
```

### /spark command
```python
def cmd_spark(self, args) -> str:
    """Get link to Spark app."""
    spark_apps = {
        'trading': 'Trading Dashboard',
        'agents': 'Agent Monitor',
        'risk': 'Risk Control Panel'
    }
    
    if not args:
        app_list = "\n".join([f"• {name}" for name in spark_apps.keys()])
        return f"""🌟 **Available Spark Apps**

{app_list}

Usage: /spark <app-name>
See docs/GITHUB_SPARK_INTEGRATION.md for details
"""
    
    app_name = args[0].lower()
    if app_name not in spark_apps:
        return f"❌ Unknown Spark app: {app_name}"
    
    app_title = spark_apps[app_name]
    return f"""🌟 **{app_title}**

Create this Spark app:
1. Go to https://github.com/spark
2. Use the prompt from spark/{app_name}_*.md
3. Connect to yaya1738/hands-off-engine

See docs/GITHUB_SPARK_INTEGRATION.md for full guide
"""
```

## Registering New Commands

Add these to the `commands` dict in `__init__`:

```python
self.commands = {
    # ... existing commands ...
    '/tasks': self.cmd_tasks,
    '/task-status': self.cmd_task_status,
    '/spark': self.cmd_spark,
}
```

Update help text to include new commands:

```python
def cmd_help(self, args) -> str:
    return """🤖 **Hands-Off Engine Bot**

**System Status:**
/status - Full system status
/metrics - Performance metrics (24h)
/health - Health check results
/agents - AI agent coordination

**Task Management:**
/task <desc> - Create new task
/tasks - List open Copilot tasks
/task-status <id> - Get task status

**Approvals:**
/pending - Show pending approvals
/approve <id> - Approve change
/reject <id> - Reject change

**GitHub Spark:**
/spark <app> - Get Spark app link

**Other:**
/help - This message
"""
```

## Testing

Test the new commands:
```bash
# List tasks
echo "/tasks" | python telegram/telegram_command_bot.py

# Check specific task
echo "/task-status 42" | python telegram/telegram_command_bot.py

# Get Spark app link
echo "/spark trading" | python telegram/telegram_command_bot.py
```

---

**Status:** Specification complete, implementation pending
**Last Updated:** 2025-12-01
