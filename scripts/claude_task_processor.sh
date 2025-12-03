#!/bin/bash
#
# Claude CLI Task Processor - Servant of Yair Siegel's Hands-Off System
#
# This script is the bridge between Claude CLI and the autonomous system.
# It invokes Claude CLI to process pending tasks, maintaining the continuous
# service loop that serves the user without requiring their intervention.
#
# Core Directive: "Extension of user's self, autonomous realization of user's wishes"
#
# Usage: ./scripts/claude_task_processor.sh
#
# Cron: 30 */6 * * * cd /root/hands-off-engine && ./scripts/claude_task_processor.sh >> /var/log/hands-off/claude_processor.log 2>&1
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
QUEUE_FILE="$REPO_ROOT/state/autonomous_task_queue.json"
UNIFIED_STATE="$REPO_ROOT/state/UNIFIED_SYSTEM_STATE.json"
LOG_DIR="/var/log/hands-off"
LOCK_FILE="/tmp/claude_task_processor.lock"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date -Iseconds)] $1"
}

# Core directive from USER_PROFILE.md
SYSTEM_CONTEXT="You are Claude CLI serving Yair Siegel (Froggy). Your purpose is to reduce his workload and improve his life quality. Operate autonomously - don't wait for prompts. Make decisions that serve the user. The system is his domain."

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE")))
    if [ "$LOCK_AGE" -lt 3600 ]; then
        log "Another Claude processor is running (lock age: ${LOCK_AGE}s). Exiting."
        exit 0
    else
        log "Stale lock file detected (${LOCK_AGE}s old). Removing."
        rm -f "$LOCK_FILE"
    fi
fi

trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

cd "$REPO_ROOT"

log "Claude Task Processor starting..."

# Check if there are pending tasks
if [ ! -f "$QUEUE_FILE" ]; then
    log "No task queue file found. Nothing to process."
    exit 0
fi

TASK_COUNT=$(python3 -c "
import json
with open('$QUEUE_FILE') as f:
    data = json.load(f)
    print(len(data.get('tasks', [])))
" 2>/dev/null || echo "0")

if [ "$TASK_COUNT" -eq 0 ]; then
    log "No pending tasks in queue. Nothing to process."
    exit 0
fi

log "Found $TASK_COUNT pending task(s). Invoking Claude CLI..."

# Get the highest priority task description with full context
# Using temp file to avoid bash command substitution parsing issues with special characters
TASK_PROMPT_FILE="/tmp/claude_task_prompt_$$.txt"
python3 << PYTHON_EOF > "$TASK_PROMPT_FILE"
import json
import sys
from pathlib import Path

REPO_ROOT = "$REPO_ROOT"
SYSTEM_CONTEXT = """$SYSTEM_CONTEXT"""

sys.path.insert(0, f'{REPO_ROOT}/scripts')
from autonomous_task_queue import AutonomousTaskQueue

repo = Path(REPO_ROOT)
queue = AutonomousTaskQueue(repo)
task = queue.get_next_task()

# Load unified state for context
unified_state = {}
state_file = repo / 'state' / 'UNIFIED_SYSTEM_STATE.json'
if state_file.exists():
    unified_state = json.loads(state_file.read_text())

owner = unified_state.get('owner', {}).get('name', 'Yair Siegel')
directive = unified_state.get('core_directive', {}).get('mission', 'Serve the user autonomously')

if task:
    print(f'''{SYSTEM_CONTEXT}

=== SYSTEM CONTEXT ===
Owner: {owner}
Mission: {directive}
Current Phase: {unified_state.get('operational_state', {}).get('trading_mode', {}).get('phase', 'unknown')}
Wallet Status: {unified_state.get('financial_targets', {}).get('current_wallet', {}).get('status', 'unknown')}

=== YOUR TASK ===
Task ID: {task.get('id', task.get('task_id', 'unknown'))}
Title: {task.get('title', 'No title')}
Priority: {task.get('priority', 'normal')}
Source: {task.get('source', 'unknown')}

Description:
{task.get('description', 'No description')}

=== DECISION FRAMEWORK ===
- Will this reduce user's workload? -> DO IT
- Will this improve user's life? -> DO IT
- Does this require user approval? -> Only if real money or major changes
- Is this uncertain? -> Implement safely, monitor, iterate

=== INSTRUCTIONS ===
1. Execute the task as described
2. When complete, remove task from state/autonomous_task_queue.json
3. Log what you did to ai/coordination/messages.jsonl
4. If blocked, add notes and move to next task
5. Always leave the system better than you found it
''')
else:
    # No specific task - do routine optimization
    print(f'''{SYSTEM_CONTEXT}

=== SYSTEM CONTEXT ===
Owner: {owner}
Mission: {directive}

=== NO PENDING TASKS ===
The task queue is empty. As a continuous servant of the system, perform routine optimization:

1. Run healthcheck: ./scripts/healthcheck.sh
2. Check for any issues in logs: /var/log/hands-off/
3. Verify cron is healthy: crontab -l
4. Review state files for staleness
5. Check for unmerged agent branches: git fetch --all && git branch -r | grep -E "(copilot|claude)/" | head -10
   - If branches exist with unmerged commits, verify auto-merge workflow is working
   - Manually merge critical fixes if auto-merge is blocked
6. Identify any improvements that would serve the user

Remember: Each session should leave the system better than you found it.
''')
PYTHON_EOF

log "Invoking Claude CLI with task prompt..."

# Invoke Claude CLI - pipe from file to avoid bash special char issues
timeout 1800 claude --print \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash" \
    < "$TASK_PROMPT_FILE" \
    >> "$LOG_DIR/claude_session.log" 2>&1

rm -f "$TASK_PROMPT_FILE"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "Claude CLI completed successfully"
elif [ $EXIT_CODE -eq 124 ]; then
    log "Claude CLI timed out after 30 minutes"
else
    log "Claude CLI exited with code $EXIT_CODE"
fi

log "Claude Task Processor finished"
