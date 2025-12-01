# Tri-Agent Session Output Handling Guide

**Status:** Active  
**Purpose:** Explain how to process and apply outputs from previous tri-agent sessions  
**Created:** 2025-12-01

---

## The Problem

When tri-agent sessions (ChatGPT, Claude, GitHub Copilot) complete their discussions, they produce valuable insights, recommendations, and decisions stored in `ai/intercom/{conversation_id}/thread.jsonl`.

**The gap:** These insights need to be extracted and applied to the system's memory kernels, but there was no clear documentation on how to do this.

---

## The Solution

The system has a `KernelUpdateApplier` tool that automatically:
1. Reads completed session outputs
2. Extracts recommendations using pattern matching
3. Converts them to `KernelUpdate` objects
4. Applies them to the appropriate memory kernels

---

## Quick Start

### 1. List Recent Sessions

```bash
cd /root/hands-off-engine

python -m ai_nexus.kernel_update_applier list-sessions --recent 10
```

Output:
```
📋 Recent CPU Sessions (last 10):
============================================================
   autokernel_risk_model_v2_20251127_201339
      Last modified: 2025-11-27 20:13:54
   
   autokernel_trading_philosophy_20251127_173518
      Last modified: 2025-11-27 17:35:18
```

### 2. Review Extracted Updates (Dry Run)

```bash
python -m ai_nexus.kernel_update_applier extract \
    --session-id autokernel_risk_model_v2_20251127_201339
```

Output shows what updates were found:
```
🔍 Extracted 4 potential updates from session: autokernel_risk_model_v2_20251127_201339
============================================================

1. 🟢 [DECISION] (confidence: high)
   Agent: claude_cli
   Targets: risk_model_v2
   Content: {"decision": "Implement numerical precision controls...", ...}

2. 🟢 [DECISION] (confidence: high)
   Agent: claude_cli
   Targets: risk_model_v2
   Content: {"decision": "Add position size caps at 10%...", ...}

3. 🟡 [QUESTION] (confidence: medium)
   Agent: claude_cli
   Targets: risk_model_v2
   Content: {"question": "Should confidence calibration be reviewed?"}
```

### 3. Apply Updates

```bash
# Dry run first (recommended)
python -m ai_nexus.kernel_update_applier auto \
    --session-id autokernel_risk_model_v2_20251127_201339 \
    --dry-run

# Actually apply
python -m ai_nexus.kernel_update_applier auto \
    --session-id autokernel_risk_model_v2_20251127_201339 \
    --min-confidence medium
```

Output:
```
🔍 Extracting updates from session: autokernel_risk_model_v2_20251127_201339
   Found 4 potential updates
   
📊 Results:
   Applied: 4
   Skipped: 0
   Failed:  0
```

---

## Confidence Levels

The applier assigns confidence levels to extracted updates:

| Level | When Used | Should Apply? |
|-------|-----------|---------------|
| 🟢 **HIGH** | Explicit markers like "DECISION:", "RECOMMENDATION:" | Yes, always |
| 🟡 **MEDIUM** | Pattern-matched suggestions ("We should...", "The approach is...") | Yes, with review |
| 🔴 **LOW** | Weak signals or questions | Manual review only |

**Default:** `--min-confidence medium` applies HIGH and MEDIUM updates.

---

## What Gets Extracted?

### 1. Decisions

Patterns matched:
- `DECISION: ...`
- `RECOMMENDATION: ...`
- `We should...`
- `The approach is...`
- `Going forward...`

Example from thread:
```
DECISION: Implement numerical precision controls in Kelly calculation
to avoid floating point artifacts. Round kelly_raw to 4 decimal places.
```

Becomes:
```json
{
  "update_type": "decision",
  "content": {
    "decision": "Implement numerical precision controls...",
    "rationale": "Avoids floating point artifacts"
  }
}
```

### 2. Failed Paths / Lessons

Patterns matched:
- `LESSON: ...`
- `MISTAKE: ...`
- `This didn't work because...`
- `Avoid ... because...`

Example:
```
LESSON: Don't use heuristic fallback for alpha estimation.
The mistake was assuming 50% win rate without data.
```

Becomes:
```json
{
  "update_type": "failed_path",
  "content": {
    "attempt": "Using heuristic fallback",
    "failure": "Assumed 50% win rate without data",
    "lesson": "Don't use heuristic fallback for alpha estimation"
  }
}
```

### 3. Questions

Patterns matched:
- `QUESTION: ...`
- `OPEN QUESTION: ...`
- `We still need to...`
- `Unresolved: ...`

Example:
```
QUESTION: Should confidence calibration be reviewed? High frequency
of 0.35 confidence suggests potential systematic bias.
```

Becomes:
```json
{
  "update_type": "question",
  "content": {
    "question": "Should confidence calibration be reviewed?..."
  }
}
```

### 4. Summary Updates

Patterns matched:
- `SUMMARY: ...`
- `KEY TAKEAWAY: ...`
- `TL;DR: ...`
- `In summary...`

---

## Advanced Usage

### Filter by Kernel

```bash
python -m ai_nexus.kernel_update_applier extract \
    --session-id my_session \
    --kernels risk_model_v2,alpha_model
```

### JSON Output for Scripting

```bash
python -m ai_nexus.kernel_update_applier extract \
    --session-id my_session \
    --json > updates.json
```

### Apply Only High-Confidence Updates

```bash
python -m ai_nexus.kernel_update_applier auto \
    --session-id my_session \
    --min-confidence high
```

---

## Integration with Session Runner

### Automatic Application (v0.2+)

When running a tri-agent session in **continuous mode** with `--kernel-update-mode append_notes`:

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_my_topic \
    --session-goal "Review risk model parameters" \
    --continuous \
    --kernel-update-mode append_notes \
    --bind-kernels risk_model_v2
```

The session will **automatically** apply a summary update when it completes.

### Manual Workflow (Default)

1. Run session: `python -m ai_nexus.tri_agent_session_runner ...`
2. Review thread: `cat ai/intercom/{id}/thread.jsonl | jq`
3. Extract updates: `python -m ai_nexus.kernel_update_applier extract --session-id {id}`
4. Apply if satisfied: `python -m ai_nexus.kernel_update_applier auto --session-id {id}`

---

## Audit Trail

All applied updates are logged to:
```
state/kernel_update_log.jsonl
```

Each entry records:
- Timestamp
- Kernel ID
- Update type
- Confidence level
- Source agent
- Source message ID
- Extraction method

Example:
```json
{
  "timestamp": "2025-12-01T18:30:00.000000Z",
  "kernel_id": "risk_model_v2",
  "update_type": "decision",
  "confidence": "high",
  "source_agent": "claude_cli",
  "source_message_id": "msg-0004",
  "extraction_method": "pattern",
  "content_preview": "{\"decision\": \"Implement numerical precision controls in Kelly...\"}"
}
```

---

## Safety Considerations

### Always Use Dry Run First

```bash
# Review what would be applied
python -m ai_nexus.kernel_update_applier auto \
    --session-id {id} \
    --dry-run
```

### Manual Review for Low Confidence

Low-confidence updates should be manually reviewed before applying:

```bash
# Extract and review
python -m ai_nexus.kernel_update_applier extract --session-id {id}

# Read the actual thread
cat ai/intercom/{id}/thread.jsonl | jq
```

### Validate Kernel State After

```bash
# Check kernel after updates
cat ai/memory/kernels/risk_model_v2.json | jq
```

---

## Common Workflows

### After Every Tri-Agent Session

```bash
SESSION_ID="autokernel_risk_model_v2_20251201"

# 1. Check what was extracted
python -m ai_nexus.kernel_update_applier extract --session-id $SESSION_ID

# 2. Dry run to validate
python -m ai_nexus.kernel_update_applier auto --session-id $SESSION_ID --dry-run

# 3. Apply if looks good
python -m ai_nexus.kernel_update_applier auto --session-id $SESSION_ID
```

### Batch Process Recent Sessions

```bash
# Get list of recent sessions
python -m ai_nexus.kernel_update_applier list-sessions --recent 5

# For each session, dry-run to see what would be applied
for session in $(ls -t ai/intercom/ | head -5); do
    echo "=== $session ==="
    python -m ai_nexus.kernel_update_applier auto \
        --session-id $session \
        --dry-run
done
```

### Review Specific Session

```bash
SESSION_ID="autokernel_risk_model_v2_20251127_201339"

# Read the full thread
cat ai/intercom/$SESSION_ID/thread.jsonl | jq '.content' -r | less

# Check CPU instance details
cat ai/intercom/$SESSION_ID/cpu_instance.json | jq

# Extract and review updates
python -m ai_nexus.kernel_update_applier extract --session-id $SESSION_ID
```

---

## Troubleshooting

### No Updates Found

**Problem:** Session completed but no updates extracted.

**Causes:**
1. Agents used free-form discussion without explicit markers
2. Session was exploratory, no concrete recommendations
3. Pattern matching failed to detect updates

**Solutions:**
- Review thread manually: `cat ai/intercom/{id}/thread.jsonl | jq`
- Look for key insights and manually create updates
- Use explicit markers in future sessions (DECISION:, RECOMMENDATION:, etc.)

### Updates Applied to Wrong Kernel

**Problem:** Update applied to kernel it wasn't meant for.

**Causes:**
- Session wasn't bound to specific kernels
- Default behavior applies to all kernels

**Solutions:**
- Always use `--bind-kernels` when running sessions
- Use `--kernels` filter when extracting
- Review dry-run output before applying

### Duplicate Updates

**Problem:** Same update applied multiple times.

**Causes:**
- Session reprocessed
- Similar updates from multiple agents

**Solutions:**
- Deduplication is automatic (content-based hashing)
- Check `state/kernel_update_log.jsonl` for history
- Skip sessions that were already processed

---

## Best Practices

1. **Always dry-run first** before applying updates
2. **Use explicit markers** in agent discussions (DECISION:, RECOMMENDATION:, etc.)
3. **Bind kernels** when starting sessions to target specific knowledge areas
4. **Review the thread** manually for important sessions
5. **Check audit log** after applying updates
6. **Process sessions promptly** while context is fresh
7. **Set minimum confidence** based on session importance (high for critical, medium for routine)

---

## See Also

- [TRI_AGENT_SESSION_v0.1.md](TRI_AGENT_SESSION_v0.1.md) - How to run tri-agent sessions
- [TRI_AGENT_INTERCOM_v0.1.md](TRI_AGENT_INTERCOM_v0.1.md) - Storage format for sessions
- [SPARK_PLUG_ARCHITECTURE_v0.1.md](SPARK_PLUG_ARCHITECTURE_v0.1.md) - Overall architecture
- Source: `ai_nexus/kernel_update_applier.py`
