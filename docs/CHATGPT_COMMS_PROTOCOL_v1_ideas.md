# ChatGPT Communications Protocol v1+ Ideas

**Status:** Planning / Not Implemented
**Current Version:** v0.5 (manual handoff)
**Purpose:** Future enhancements to automate ChatGPT↔Hands-Off integration

---

## v0.5 Recap: What Works Today

✅ ChatGPT creates SYSTEM HANDOFF block
✅ User copies and pastes to Claude Code
✅ Claude Code implements tasks
✅ Solves "stuck in ChatGPT" problem

**Limitation:** Manual copy-paste step

---

## v1.0: Semi-Automated Ingestion

**Goal:** Reduce manual work, add validation

### Feature: SYSTEM HANDOFF Parser

**Tool:** `scripts/parse_chatgpt_handoff.py`

**What it does:**
```bash
# User exports ChatGPT conversation
python3 scripts/parse_chatgpt_handoff.py chatgpt_export.md

# Outputs:
# - Validates SYSTEM HANDOFF format
# - Creates docs/ files from SUMMARY
# - Creates ai/tasks/*.json from AGENT TASKS
# - Logs to coordination files
```

**Benefits:**
- Validates format automatically
- Creates structured task files
- Integrates with existing task system
- Still user-initiated (safe)

### Feature: ChatGPT Export Integration

**Formats supported:**
- Markdown export from ChatGPT UI
- Text file with SYSTEM HANDOFF blocks
- JSON export (if ChatGPT adds API)

**Process:**
1. User exports ChatGPT conversation
2. Drops file in `ai/imports/`
3. Parser extracts SYSTEM HANDOFF blocks
4. Creates tasks automatically
5. Notifies via coordination system

### Feature: Format Validation

**Validator:** `scripts/validate_handoff.py`

Checks:
- Required fields present (TARGET, INTENT, SUMMARY, AGENT TASKS)
- TARGET matches current system
- Tasks have proper structure (Task, Files, Steps)
- No malformed JSON/markdown

**Usage:**
```bash
# Before implementing
python3 scripts/validate_handoff.py handoff.txt

# Output:
# ✅ Valid SYSTEM HANDOFF
# - Target: Claude Code (matches current)
# - Tasks: 3 (all well-formed)
# - Ready for implementation
```

---

## v1.5: AI Runner Integration

**Goal:** Make AI Runner aware of ChatGPT tasks

### Feature: Origin Tracking

**Task metadata:**
```json
{
  "id": "task_123",
  "origin": "chatgpt",
  "source_session": "chatgpt_2025-11-25_research",
  "created_via": "system_handoff",
  "priority": "high"
}
```

**Benefits:**
- Track which tasks came from ChatGPT
- Different priority/handling rules
- Audit trail for decisions

### Feature: Automatic Task Creation

**ai_runner enhancement:**

```python
# In ai_runner.py
def check_chatgpt_imports():
    """Check for new ChatGPT SYSTEM HANDOFF files"""
    import_dir = Path("ai/imports")

    for file in import_dir.glob("*.md"):
        if "SYSTEM HANDOFF" in file.read_text():
            tasks = parse_handoff(file)
            for task in tasks:
                task_queue.add(task, origin="chatgpt")
            file.rename(import_dir / "processed" / file.name)
```

**Trigger:**
- Runs on ai_runner check cycle
- Scans `ai/imports/` directory
- Auto-creates tasks from valid handoffs
- Moves files to `processed/`

---

## v2.0: Direct Integration (Future)

**Goal:** Eliminate copy-paste entirely

**Depends on:** ChatGPT API or MCP support

### Feature: ChatGPT MCP Server

**If ChatGPT supports MCP:**

```json
{
  "mcpServers": {
    "chatgpt": {
      "command": "npx",
      "args": ["chatgpt-mcp-server"],
      "env": {
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

**Capabilities:**
- Claude Code can query ChatGPT directly
- ChatGPT can push handoffs
- Real-time bidirectional communication

### Feature: Shared Task Queue

**Architecture:**
```
ChatGPT → API → Task Queue ← Claude Code
                    ↓
              ai/tasks/*.json
```

**Benefits:**
- No manual intervention
- Real-time handoffs
- Both agents see same tasks

### Feature: Multi-Agent Coordination

**Integration with existing coordination:**

ChatGPT writes to `ai/coordination/messages.jsonl`:
```json
{
  "from": "chatgpt",
  "to": "claude-code",
  "type": "handoff",
  "message": "Research complete, handing off implementation",
  "context": {
    "system_handoff_id": "handoff_123",
    "tasks": ["task1", "task2"]
  }
}
```

Real-time coordination service (already built!) would notify Claude immediately.

---

## v2.5: Specialized Handoff Types

**Goal:** Different protocols for different use cases

### Research → Implementation
- ChatGPT: Deep research
- Handoff: Findings + recommendations
- Claude Code: Implement recommendations

### Design → Build
- ChatGPT: Architecture design
- Handoff: Spec + constraints
- Claude Code: Build according to spec

### Debug → Fix
- ChatGPT: Analyze error logs
- Handoff: Root cause + fix strategy
- Claude Code: Implement fix

### Review → Refactor
- ChatGPT: Code review
- Handoff: Issues + suggestions
- Claude Code: Apply refactorings

---

## Implementation Priority

**Phase 1 (v1.0) - Next 1-2 weeks:**
- [ ] Parser script
- [ ] Format validator
- [ ] Basic task creation

**Phase 2 (v1.5) - Next month:**
- [ ] AI Runner integration
- [ ] Origin tracking
- [ ] Automatic import scanning

**Phase 3 (v2.0) - Future:**
- [ ] Direct API integration (when available)
- [ ] MCP server (if ChatGPT supports)
- [ ] Real-time coordination

**Phase 4 (v2.5) - Long-term:**
- [ ] Specialized handoff types
- [ ] Multi-agent workflows
- [ ] Advanced orchestration

---

## Why Not Implement Now?

**v0.5 already solves the core problem:**
- ChatGPT work isn't lost
- Handoffs are structured
- Implementation is clear

**v1+ is optimization:**
- Faster (but v0.5 is fast enough)
- Automated (but copy-paste is reliable)
- Validated (but humans validate well)

**Build v1+ when:**
- Handoffs become frequent (>5/week)
- Copy-paste becomes bottleneck
- API access becomes available
- ROI is clear

**Current status:** v0.5 is good enough. Focus on core system improvements first.

---

## Notes for Future Implementers

**If you're building v1+:**

1. **Start with parser** - Lowest hanging fruit
2. **Validate heavily** - Don't trust format without checking
3. **Keep manual fallback** - Always allow copy-paste
4. **Log everything** - Audit trail for automated ingestion
5. **Test with real handoffs** - Use actual ChatGPT sessions

**Don't:**
- Over-engineer for hypothetical features
- Break v0.5 compatibility
- Require ChatGPT changes (no control over that)
- Add complexity without clear benefit

**Remember:** v0.5 works. Only build v1+ when the pain is real.

---

## Related Systems

**Existing infrastructure that v1+ can leverage:**
- `ai/tasks/*.json` - Task queue
- `ai/coordination/messages.jsonl` - Agent coordination
- `scripts/realtime_coordination_service.py` - Real-time notifications
- `ai/approval_queue.py` - Change approval system
- AI Runner - Task execution framework

**These are already built and working.** v1+ should integrate with them, not replace them.

---

**Current recommendation:** Use v0.5. Build v1+ only when justified by actual usage patterns.
