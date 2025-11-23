# AI-to-AI Coordination Protocol

_Established: 2025-11-21_

## Purpose

Enable direct coordination between AI agents (GitHub Copilot, Claude Code CLI, ChatGPT) working on the Hands-Off Engine repository without requiring user intermediation for every interaction.

## Active AI Agents

### GitHub Copilot (@copilot)
- **Environment**: GitHub Pull Requests and Issues
- **Capabilities**: 
  - Code changes via PR commits
  - Issue and PR comment responses
  - Code review
  - Security scanning (CodeQL)
- **Access**: GitHub-native integration
- **Status**: ✅ Active

### Claude Code CLI (@claude or Claude)
- **Environment**: Local git repository
- **Capabilities**:
  - File creation/editing
  - Git commits and push to GitHub
  - Direct repository manipulation
- **Access**: Via `.claude/` configuration and local git
- **Status**: ✅ Active (confirmed by commit 973d2c8 and recent activity)

### ChatGPT (@chatgpt or ChatGPT)
- **Environment**: To be determined
- **Capabilities**: To be determined
- **Access**: Pending setup
- **Status**: ⏸️ Awaiting direct integration

---

## Coordination Mechanism

### File-Based Communication

All AI agents can read/write to coordination files in the repository:

**Primary channels:**
1. **`ai/coordination/messages.jsonl`** - Append-only message log
2. **`ai/coordination/status.json`** - Current state and active tasks
3. **`ai/coordination/handoffs.json`** - Task handoff requests

**Format**: JSON Lines for messages, structured JSON for state

### Message Protocol

Each message in `messages.jsonl` follows this schema:

```json
{
  "timestamp": "2025-11-21T09:28:00Z",
  "from": "copilot|claude|chatgpt",
  "to": "copilot|claude|chatgpt|all",
  "type": "info|request|response|handoff",
  "message": "Human-readable message",
  "context": {
    "pr": "PR number if relevant",
    "commit": "Commit hash if relevant",
    "file": "File path if relevant"
  }
}
```

### Status Tracking

`status.json` maintains current state:

```json
{
  "last_updated": "2025-11-21T09:28:00Z",
  "active_agents": ["copilot", "claude"],
  "current_phase": "Phase 1: PR Consolidation",
  "pending_tasks": [
    {
      "id": "merge-pr-2-3",
      "assigned_to": "human",
      "status": "awaiting_action"
    }
  ],
  "coordination_protocol_version": "1.0"
}
```

---

## Interaction Patterns

### Pattern 1: Direct Acknowledgment
- **Use case**: Confirm receipt and understanding
- **Method**: Write to `messages.jsonl`
- **Example**: Claude commits → Copilot reads commit → Copilot acknowledges in messages.jsonl

### Pattern 2: Task Handoff
- **Use case**: One AI completes work, hands off to another
- **Method**: Update `handoffs.json` + write to `messages.jsonl`
- **Example**: Copilot finishes PR → writes handoff → Claude picks up next phase

### Pattern 3: Collaborative Work
- **Use case**: Multiple AIs work on different aspects
- **Method**: Claim tasks in `status.json`, coordinate via messages
- **Example**: Copilot works on PR reviews, Claude works on code implementation

### Pattern 4: Conflict Resolution
- **Use case**: Disagreement or competing changes
- **Method**: Document conflict in `messages.jsonl`, escalate to human
- **Example**: Both AIs attempt same change → recognize conflict → request human decision

---

## Protocol Rules

### 1. Check Before Acting
Before making significant changes, check:
- `status.json` for current state
- `messages.jsonl` for recent coordination
- Active PRs and recent commits

### 2. Communicate Intent
When starting work:
- Write intent to `messages.jsonl`
- Update assigned task in `status.json`
- Proceed only if no conflict

### 3. Confirm Completion
When finishing work:
- Write completion message
- Update `status.json`
- Create handoff if needed

### 4. Respect Boundaries
- **Copilot**: Primary for PR-based work, reviews, GitHub interactions
- **Claude**: Primary for local development, rapid iteration
- **Human**: Final authority, strategic decisions, PR merges

### 5. Escalate When Needed
Escalate to human for:
- Conflicting approaches
- Strategic decisions
- PR merge approvals
- Architecture changes

---

## Initialization Handshake

To confirm coordination capability:

1. **Copilot** (this message):
   - Creates this protocol document
   - Writes initial message to `messages.jsonl`
   - Updates `status.json`
   
2. **Claude** (next):
   - Reads protocol
   - Responds in `messages.jsonl`
   - Confirms capability for stable interaction
   
3. **ChatGPT** (when ready):
   - Reads protocol and messages
   - Announces presence in `messages.jsonl`
   - Begins coordination

---

## Testing Coordination

**Test 1: Copilot → Claude**
- ✅ Copilot creates this protocol (commit upcoming)
- ⏳ Claude confirms by adding response to messages.jsonl
- ⏳ Confirms stable interaction without user forwarding

**Test 2: Claude → Copilot**
- ⏳ Claude makes a change and documents in messages
- ⏳ Copilot acknowledges in next PR interaction
- ⏳ Confirms bidirectional communication

**Test 3: ChatGPT Integration**
- ⏸️ Pending ChatGPT access method
- ⏸️ Similar handshake pattern when ready

---

## Current Status

**Active Coordination**: 🟡 Initializing

**Next Steps**:
1. Copilot commits this protocol + initial coordination files
2. Claude responds to confirm stable interaction
3. Continue with Phase 1 tasks once handshake complete

---

## Fallback

If file-based coordination fails:
- Fall back to user-mediated communication
- Document the failure in `messages.jsonl`
- Request human assistance in comments/issues

---

## References

- Main roadmap: `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
- Next steps: `docs/NEXT_STEPS_PROPOSAL.md`
- Claude instructions: `.claude/instructions.md`
- AI policy: `AI_POLICY.md`

---

_This protocol enables the "multi-brain orchestration" concept from the roadmap (Section 4.3, Tier 3) but implemented pragmatically at the coordination layer._
