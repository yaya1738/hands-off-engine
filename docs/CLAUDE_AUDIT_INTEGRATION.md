# Claude Code CLI Audit Integration

## Overview

This document describes how Claude Code CLI actions are tracked and audited in the Hands-Off Engine system.

**Status**: ✅ OPERATIONAL

**Last Updated**: 2025-12-01

---

## Architecture

Claude Code CLI actions are logged through a two-layer audit system:

1. **Audit Logger** (`audit/audit_logger.py`) - Event-based logging
2. **Financial Ledger** (`audit/ledger.py`) - Cost tracking with hash-chaining

```
Claude Code CLI Action
    ↓
claude_audit_helper.py
    ↓
ClaudeProvider.log_action()
    ↓
├─→ AuditLogger.log_event()  → audit/logs/ai_claude.jsonl
└─→ FinancialLedger.add_cost() → audit/ledger.jsonl
```

---

## Components

### 1. ClaudeProvider (`ai_nexus/provider_claude.py`)

The ClaudeProvider class tracks Claude Code CLI operations:

```python
from ai_nexus import ClaudeProvider
from audit import AuditLogger, FinancialLedger

audit_logger = AuditLogger()
ledger = FinancialLedger()
claude = ClaudeProvider(audit_logger, ledger)

# Log a Claude action
claude.log_action(
    action="code_generation",
    files_changed=3,
    lines_added=150,
    lines_removed=50,
    tokens_used=5000,  # Optional
    metadata={"feature": "new_api_endpoint"}
)
```

### 2. Claude Audit Helper (`scripts/claude_audit_helper.py`)

Command-line tool for logging Claude actions from shell scripts:

```bash
# Log a code generation action
python3 scripts/claude_audit_helper.py log_action \
    --action "code_generation" \
    --files-changed 3 \
    --lines-added 150 \
    --lines-removed 50 \
    --verbose

# Log with tokens and metadata
python3 scripts/claude_audit_helper.py log_action \
    --action "code_review" \
    --files-changed 5 \
    --tokens-used 2000 \
    --metadata '{"pr_number": 42}' \
    --verbose
```

### 3. Claude Audit Checker (`audit/claude_audit_checker.py`)

Verification tool to audit the Claude CLI integration:

```bash
# Run full audit check
python3 audit/claude_audit_checker.py --verbose

# Check specific session
python3 audit/claude_audit_checker.py --session <session-id>

# Save report to file
python3 audit/claude_audit_checker.py --output audit_report.txt
```

---

## Integration Points

### Claude Orchestrator (`scripts/claude_orchestrator.py`)

The orchestrator now logs:
- Task queue additions
- Orchestrator invocations
- Success/failure outcomes

```python
# Already integrated - logs automatically when tasks are queued
```

### Shell Scripts

To integrate audit logging into shell scripts:

```bash
#!/bin/bash
# Your Claude Code CLI wrapper

# ... do work ...

# Log the action
python3 scripts/claude_audit_helper.py log_action \
    --action "your_action_name" \
    --files-changed ${FILES_CHANGED} \
    --lines-added ${LINES_ADDED} \
    --lines-removed ${LINES_REMOVED}
```

**Example Integration for `claude_sync.sh`:**

```bash
# At the end of successful sync
if [ $? -eq 0 ]; then
    python3 scripts/claude_audit_helper.py log_action \
        --action "sync_completed" \
        --metadata "{\"instance\": \"$WHO\"}"
fi
```

**Example Integration for `claude_task_processor.sh`:**

```bash
# After task completion
python3 scripts/claude_audit_helper.py log_action \
    --action "task_completed" \
    --files-changed $FILES_CHANGED \
    --lines-added $LINES_ADDED \
    --lines-removed $LINES_REMOVED \
    --metadata "{\"task_id\": \"$TASK_ID\"}"
```

---

## Tracked Metrics

For each Claude action, the system tracks:

| Metric | Description | Source |
|--------|-------------|--------|
| **action** | Type of action performed | User-specified |
| **files_changed** | Number of files modified | User-specified |
| **lines_added** | Lines of code added | User-specified |
| **lines_removed** | Lines of code removed | User-specified |
| **tokens_used** | Tokens consumed (if known) | User-specified or estimated |
| **cost** | Estimated cost in USD | Auto-calculated |
| **timestamp** | When action occurred | Auto-generated |
| **session_id** | Session identifier | Auto-generated |

---

## Cost Estimation

When tokens are not provided, costs are estimated based on code changes:

```python
# Rough estimate: lines of code ≈ tokens
tokens_used = (lines_added + lines_removed) * 5

# Using Claude 3.5 Sonnet pricing
pricing = {
    "input": 3.0,   # per 1M tokens
    "output": 15.0  # per 1M tokens
}
```

For more accurate cost tracking, provide actual token counts when available.

---

## Action Types

Common action types for Claude Code CLI:

| Action | Description | When to Use |
|--------|-------------|-------------|
| `code_generation` | New code created | When Claude generates new functionality |
| `code_review` | Code reviewed | When Claude reviews PR or code |
| `code_refactor` | Code refactored | When Claude refactors existing code |
| `bug_fix` | Bug fixed | When Claude fixes a bug |
| `optimization` | Code optimized | When Claude optimizes performance |
| `documentation` | Documentation updated | When Claude updates docs |
| `task_queued` | Task added to queue | When orchestrator queues work |
| `task_completed` | Task completed | When Claude finishes a task |
| `sync_completed` | Sync operation done | When coordination sync completes |

---

## Viewing Audit Logs

### View Recent Claude Events

```bash
# View last 50 events
python3 audit/audit_viewer.py --component ai.claude

# View with metadata
python3 audit/audit_viewer.py --component ai.claude --metadata

# View session summary
python3 audit/audit_viewer.py --session <session-id> --summary
```

### Check Audit Health

```bash
# Run comprehensive audit check
python3 audit/claude_audit_checker.py --verbose
```

**Exit codes:**
- `0` - All checks pass
- `1` - Critical issues found
- `2` - Warnings found (non-critical)

---

## Best Practices

### 1. Log All Significant Actions

Every time Claude Code CLI performs work, log it:

```python
# After Claude generates code
log_claude_action(
    action="code_generation",
    files_changed=len(modified_files),
    lines_added=additions,
    lines_removed=deletions
)
```

### 2. Include Metadata

Add context to help with analysis:

```python
log_claude_action(
    action="bug_fix",
    files_changed=1,
    lines_added=5,
    metadata={
        "issue_number": 42,
        "severity": "high",
        "component": "executor"
    }
)
```

### 3. Use Consistent Action Names

Stick to the standard action types for better reporting.

### 4. Provide Token Counts When Available

If Claude reports token usage, pass it for accurate cost tracking:

```python
log_claude_action(
    action="code_review",
    tokens_used=actual_tokens_from_claude
)
```

### 5. Run Regular Audits

Check audit health periodically:

```bash
# Daily audit check
python3 audit/claude_audit_checker.py --output /tmp/daily_audit.txt
```

---

## Troubleshooting

### No Events Logged

If `claude_audit_checker.py` shows no events:

1. Check that audit system is importable:
   ```bash
   python3 -c "from audit import AuditLogger; print('OK')"
   ```

2. Verify audit directory exists:
   ```bash
   ls -la audit/logs/
   ```

3. Check permissions:
   ```bash
   chmod -R u+w audit/logs/
   ```

### Integration Not Working

If shell script integration fails:

1. Check Python path:
   ```bash
   which python3
   ```

2. Test helper script directly:
   ```bash
   python3 scripts/claude_audit_helper.py log_action \
       --action "test" --files-changed 1 --verbose
   ```

3. Check for import errors:
   ```bash
   python3 scripts/claude_audit_helper.py 2>&1 | grep -i error
   ```

### Cost Tracking Issues

If costs seem incorrect:

1. Provide actual token counts instead of estimates
2. Check pricing in `ai_nexus/provider_claude.py`
3. Verify ledger integrity:
   ```python
   from audit import FinancialLedger
   ledger = FinancialLedger()
   print(ledger.verify_integrity())
   ```

---

## Example Workflow

Complete example of logging a Claude Code CLI session:

```bash
#!/bin/bash
# claude_code_session.sh - Wrapper for Claude Code CLI

SESSION_ID=$(uuidgen)
START_TIME=$(date +%s)

# Track files before
FILES_BEFORE=$(git ls-files | wc -l)

# Run Claude Code CLI
claude-code --task "Implement feature X"

# Track files after
FILES_AFTER=$(git ls-files | wc -l)
FILES_CHANGED=$((FILES_AFTER - FILES_BEFORE))

# Get git stats
STATS=$(git diff --stat HEAD~1 | tail -1)
LINES_ADDED=$(echo $STATS | awk '{print $4}')
LINES_REMOVED=$(echo $STATS | awk '{print $6}')

# Log to audit system
python3 scripts/claude_audit_helper.py log_action \
    --action "code_generation" \
    --files-changed ${FILES_CHANGED} \
    --lines-added ${LINES_ADDED:-0} \
    --lines-removed ${LINES_REMOVED:-0} \
    --session-id ${SESSION_ID} \
    --metadata "{\"task\": \"feature_x\", \"duration\": $(($(date +%s) - START_TIME))}" \
    --verbose

# Run audit check
python3 audit/claude_audit_checker.py --session ${SESSION_ID}
```

---

## Future Enhancements

Planned improvements:

- [ ] Real-time token tracking via Claude API
- [ ] Automatic git stat collection
- [ ] Web dashboard for audit visualization
- [ ] Alerts for high-cost operations
- [ ] Budget tracking and recommendations
- [ ] Integration with CI/CD pipelines

---

## References

- **Audit System**: `AUDIT_NEXUS_SUMMARY.md`
- **Development Standards**: `docs/DEVELOPMENT_STANDARDS.md`
- **AI Nexus**: `ai_nexus/README.md`
- **Financial Ledger**: `audit/ledger.py`

---

## Support

For issues or questions:

1. Run diagnostic: `python3 audit/claude_audit_checker.py --verbose`
2. Check logs: `audit/logs/ai_claude.jsonl`
3. Review ledger: `audit/ledger.jsonl`
4. See examples: `examples/ai_nexus_demo.py`
