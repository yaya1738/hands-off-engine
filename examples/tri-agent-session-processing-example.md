# Example: Processing Tri-Agent Session Output

**Date:** 2025-12-01  
**Purpose:** Demonstrate end-to-end workflow for handling tri-agent session outputs

---

## Scenario

A tri-agent session was run to review the risk model parameters. The session produced recommendations that need to be applied to the `risk_model_v2` kernel.

---

## Step-by-Step Workflow

### 1. Run the Tri-Agent Session

```bash
cd /root/hands-off-engine

python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_risk_review \
    --session-goal "Review risk model v2 parameters and suggest improvements" \
    --rounds 2 \
    --agents chatgpt,claude_cli \
    --bind-kernels risk_model_v2
```

**Output:**
```
============================================================
TRI-AGENT BACKEND SESSION (CPU-ALIGNED)
============================================================
CPU ID: cpu_20251201_risk_review_1733074800
...
[chatgpt]: I suggest we reduce max Kelly fraction from 0.25 to 0.15...
[claude_cli]: DECISION: Set max Kelly fraction to 0.15 based on recent drawdown...
...
SESSION COMPLETE
Full thread: ai/intercom/20251201_risk_review/thread.jsonl
```

### 2. List Recent Sessions

```bash
./bin/process-agent-sessions.sh list --recent 3
```

**Output:**
```
📋 Recent CPU Sessions (last 3):
============================================================
   20251201_risk_review
      Last modified: 2025-12-01 14:30:00
   ...
```

### 3. Review What Was Extracted

```bash
./bin/process-agent-sessions.sh review 20251201_risk_review
```

**Output:**
```
ℹ Reviewing session: 20251201_risk_review

=== CPU Instance Info ===
CPU ID: cpu_20251201_risk_review_1733074800
Status: stopped
Bound Kernels: risk_model_v2
Steps: 2

=== Thread Summary ===
Messages: 5
Participants:
      1 system
      2 chatgpt
      2 claude_cli

=== Extracted Updates ===
🔍 Extracted 3 potential updates from session: 20251201_risk_review
============================================================

1. 🟢 [DECISION] (confidence: high)
   Agent: claude_cli
   Targets: risk_model_v2
   Content: {"decision": "Set max Kelly fraction to 0.15", "rationale": "Recent drawdown analysis..."}

2. 🟢 [DECISION] (confidence: high)
   Agent: claude_cli
   Targets: risk_model_v2
   Content: {"decision": "Add position caps at 10% of bankroll", ...}

3. 🟡 [QUESTION] (confidence: medium)
   Agent: chatgpt
   Targets: risk_model_v2
   Content: {"question": "Should we adjust Kelly based on market volatility?"}

View full thread? [y/N]
```

### 4. Dry-Run Application

```bash
./bin/process-agent-sessions.sh apply 20251201_risk_review --dry-run
```

**Output:**
```
ℹ Applying updates from session: 20251201_risk_review [DRY RUN]

🔍 Extracting updates from session: 20251201_risk_review
   Found 3 potential updates

📊 Results:
   Applied: 2
   Skipped: 1
   Failed:  0

ℹ To apply for real, use: process-agent-sessions.sh apply 20251201_risk_review --for-real
```

### 5. Review Dry-Run Details

The dry-run shows:
- ✅ 2 HIGH confidence decisions would be applied
- ⏭️ 1 MEDIUM confidence question was skipped (default is `--min-confidence medium` for decisions only)

### 6. Actually Apply Updates

```bash
./bin/process-agent-sessions.sh apply 20251201_risk_review --for-real
```

**Output:**
```
⚠ This will actually apply updates to kernels!
Are you sure? [y/N] y

ℹ Applying updates from session: 20251201_risk_review [LIVE MODE]

🔍 Extracting updates from session: 20251201_risk_review
   Found 3 potential updates

📊 Results:
   Applied: 2
   Skipped: 1
   Failed:  0

✓ Updates applied!
ℹ Check audit log: state/kernel_update_log.jsonl
```

### 7. Verify Updates Were Applied

```bash
# Check the kernel
cat ai/memory/kernels/risk_model_v2.json | jq '.decisions[-2:]'
```

**Output:**
```json
[
  {
    "decision": "Set max Kelly fraction to 0.15",
    "rationale": "Recent drawdown analysis shows 0.25 was too aggressive",
    "timestamp": "2025-12-01T14:35:00Z",
    "source": "auto_extracted:msg-0003",
    "agent": "claude_cli"
  },
  {
    "decision": "Add position caps at 10% of bankroll",
    "rationale": "Prevents over-concentration in high-Kelly scenarios",
    "timestamp": "2025-12-01T14:35:00Z",
    "source": "auto_extracted:msg-0003",
    "agent": "claude_cli"
  }
]
```

### 8. Check Audit Log

```bash
tail -2 state/kernel_update_log.jsonl | jq
```

**Output:**
```json
{
  "timestamp": "2025-12-01T14:35:00.123456Z",
  "kernel_id": "risk_model_v2",
  "update_type": "decision",
  "confidence": "high",
  "source_agent": "claude_cli",
  "source_message_id": "msg-0003",
  "extraction_method": "pattern",
  "content_preview": "{\"decision\": \"Set max Kelly fraction to 0.15\", \"rationale\": \"Recent drawdown analysis...\"}"
}
{
  "timestamp": "2025-12-01T14:35:01.234567Z",
  "kernel_id": "risk_model_v2",
  "update_type": "decision",
  "confidence": "high",
  "source_agent": "claude_cli",
  "source_message_id": "msg-0003",
  "extraction_method": "pattern",
  "content_preview": "{\"decision\": \"Add position caps at 10% of bankroll\", \"rationale\": \"Prevents over-concentration...\"}"
}
```

---

## Alternative: Using Python Directly

For automation/scripting:

```bash
# Extract as JSON
python -m ai_nexus.kernel_update_applier extract \
    --session-id 20251201_risk_review \
    --json > extracted_updates.json

# Review JSON
cat extracted_updates.json | jq

# Apply programmatically
python -m ai_nexus.kernel_update_applier auto \
    --session-id 20251201_risk_review \
    --min-confidence high \
    --json > application_result.json

# Check results
cat application_result.json | jq '.updates_applied'
```

---

## Tips for Agents

### Make Extraction Easy

Use explicit markers in your session output:

```
DECISION: Your decision here
RATIONALE: Why this is the right choice

LESSON: What didn't work
Because: Why it failed

QUESTION: Unresolved issue to track
```

### Bind Kernels When Running Sessions

```bash
--bind-kernels risk_model_v2,alpha_model
```

This ensures updates target the right knowledge areas.

### Review Before Applying

Always use `--dry-run` first, especially for:
- Critical system parameters
- Risk/safety settings
- Production configurations

### Use Confidence Levels

- `--min-confidence high` - Only explicit recommendations
- `--min-confidence medium` - Include pattern-matched suggestions (default)
- `--min-confidence low` - Include everything (manual review recommended)

---

## Monitoring Session Backlog

Check if there are unprocessed sessions:

```bash
# List all sessions
./bin/process-agent-sessions.sh list --recent 20

# Quick scan of recent sessions
./bin/process-agent-sessions.sh batch --recent 5
```

The batch command will:
1. Show each session
2. Extract potential updates
3. Ask if you want to review
4. Ask if you want to apply (dry-run)
5. Move to next session

---

## Summary

**Complete workflow:**
1. Run tri-agent session with `--bind-kernels`
2. List recent sessions
3. Review extracted updates
4. Dry-run application
5. Apply for real if satisfied
6. Verify kernel updates
7. Check audit log

**Time required:** 2-5 minutes per session  
**Automation potential:** High (can script the entire flow)

---

See: [docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md](TRI_AGENT_SESSION_OUTPUT_HANDLING.md) for full reference.
