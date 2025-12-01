# Quick Reference: Process Agent Session Outputs

**🎯 Purpose:** Handle insights from tri-agent (ChatGPT + Claude + Copilot) discussions

---

## One-Line Commands

```bash
# List recent sessions
./bin/process-agent-sessions.sh list

# Review specific session  
./bin/process-agent-sessions.sh review {session-id}

# Apply updates (dry-run)
./bin/process-agent-sessions.sh apply {session-id}

# Apply for real
./bin/process-agent-sessions.sh apply {session-id} --for-real

# Process recent sessions interactively
./bin/process-agent-sessions.sh batch
```

---

## What Gets Extracted?

| Pattern | Type | Confidence |
|---------|------|------------|
| `DECISION:` `RECOMMENDATION:` | Decision | 🟢 High |
| `LESSON:` `MISTAKE:` | Failed Path | 🟢 High |
| `QUESTION:` | Question | 🟢 High |
| `We should...` | Decision | 🟡 Medium |
| `This didn't work...` | Failed Path | 🟡 Medium |

---

## For Agents: Best Practice

Use explicit markers in session output:

```
DECISION: Set max Kelly fraction to 0.15
RATIONALE: Recent drawdown shows 0.25 too aggressive

LESSON: Don't override risk limits for high edge
The mistake was thinking edge compensates for size

QUESTION: Add dynamic Kelly based on volatility?
```

---

## Safety Features

- ✅ Dry-run by default
- ✅ Confirmation required for live
- ✅ Full audit trail logged
- ✅ Confidence-based filtering

---

## Files

**Docs:** `docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md`  
**Example:** `examples/tri-agent-session-processing-example.md`  
**Script:** `bin/process-agent-sessions.sh`  
**Tool:** `python -m ai_nexus.kernel_update_applier`  
**Audit:** `state/kernel_update_log.jsonl`

---

**Full guide:** [docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md](docs/TRI_AGENT_SESSION_OUTPUT_HANDLING.md)
