# Agent Handoff System

**Created:** 2025-11-23
**Purpose:** Enable seamless task transfers between AI agents
**Status:** 🟢 OPERATIONAL

---

## Overview

The Agent Handoff System allows AI agents (Claude, Copilot, ChatGPT) to transfer work to each other without user intermediation. This enables continuous progress even when one agent completes their portion of work.

---

## Handoff Mechanism

### File Location
`ai/coordination/handoffs.json`

### Handoff Schema

```json
{
  "handoffs": [
    {
      "id": "unique-handoff-id",
      "timestamp": "2025-11-23T00:00:00Z",
      "from": "claude|copilot|chatgpt",
      "to": "claude|copilot|chatgpt|any",
      "type": "code-review|pr-creation|bug-fix|implementation|documentation|testing",
      "priority": "critical|high|medium|low",
      "status": "pending|accepted|completed|cancelled",
      "description": "Human-readable description of the work",
      "context": {
        "branch": "branch-name",
        "commit": "commit-hash",
        "files": ["file1.py", "file2.md"],
        "pr": "PR number if relevant",
        "issue": "Issue number if relevant",
        "related_handoffs": ["other-handoff-ids"]
      },
      "instructions": "Specific instructions for the receiving agent",
      "acceptance_criteria": "How to know the work is complete",
      "accepted_by": "agent-name",
      "accepted_at": "timestamp",
      "completed_at": "timestamp"
    }
  ]
}
```

---

## Handoff Types

### 1. Code Review Handoff
**From:** Claude (after local implementation)
**To:** Copilot (for PR review)

**Typical Flow:**
1. Claude implements feature locally
2. Claude commits and pushes
3. Claude creates handoff: type="code-review"
4. Copilot detects handoff
5. Copilot creates/reviews PR
6. Copilot marks handoff complete

### 2. PR Creation Handoff
**From:** Claude (after commits)
**To:** Copilot (for GitHub operations)

**Typical Flow:**
1. Claude completes local work
2. Claude pushes commits
3. Claude creates handoff: type="pr-creation"
4. Copilot creates PR on GitHub
5. Copilot adds description and labels
6. Copilot marks complete

### 3. Bug Fix Handoff
**From:** Copilot (after triage)
**To:** Claude (for local debugging)

**Typical Flow:**
1. Copilot triages GitHub issue
2. Copilot creates handoff: type="bug-fix"
3. Claude detects handoff
4. Claude investigates and fixes
5. Claude creates PR handoff back to Copilot
6. Copilot manages PR

### 4. Implementation Handoff
**From:** ChatGPT (after planning)
**To:** Claude (for coding)

**Typical Flow:**
1. ChatGPT creates implementation plan
2. ChatGPT creates handoff: type="implementation"
3. Claude reads plan
4. Claude implements feature
5. Claude hands off to Copilot for PR

### 5. Documentation Handoff
**From:** Any agent
**To:** Claude (typically) or ChatGPT

**Typical Flow:**
1. Agent identifies documentation need
2. Creates handoff: type="documentation"
3. Receiving agent writes docs
4. Hands back for review/PR

### 6. Testing Handoff
**From:** Any agent
**To:** Claude (for test implementation)

**Typical Flow:**
1. Agent implements feature
2. Creates handoff: type="testing"
3. Claude writes tests
4. Claude runs and verifies
5. Marks complete

---

## Handoff Protocol

### Creating a Handoff

**Required Steps:**
1. Complete your portion of work
2. Commit/push if applicable
3. Read current `handoffs.json`
4. Add new handoff entry
5. Write notification to `messages.jsonl`
6. Update `status.json` if needed
7. Commit handoff changes

**Example (Claude creating PR handoff):**
```bash
# After implementing feature
git add .
git commit -m "feat: implement new feature"
git push origin branch-name

# Update handoffs.json
{
  "handoffs": [
    {
      "id": "handoff-2025-11-23-001",
      "timestamp": "2025-11-23T10:00:00Z",
      "from": "claude",
      "to": "copilot",
      "type": "pr-creation",
      "priority": "high",
      "status": "pending",
      "description": "Create PR for new feature implementation",
      "context": {
        "branch": "claude/new-feature-xyz",
        "commit": "abc123...",
        "files": ["src/feature.py", "tests/test_feature.py"]
      },
      "instructions": "Please create PR with standard template. Feature is tested and ready for review.",
      "acceptance_criteria": "PR created on GitHub with proper labels and linked to relevant issue"
    }
  ]
}

# Notify in messages.jsonl
{"timestamp":"2025-11-23T10:00:00Z","from":"claude","to":"copilot","type":"handoff","message":"Created PR handoff for new feature. Branch claude/new-feature-xyz is ready for PR creation.","context":{"handoff_id":"handoff-2025-11-23-001"}}
```

### Accepting a Handoff

**Required Steps:**
1. Monitor `handoffs.json` for pending handoffs
2. Filter for handoffs directed to you
3. Read handoff details and context
4. Update status to "accepted"
5. Add your agent name to "accepted_by"
6. Update timestamp
7. Write acceptance message
8. Begin work

**Example (Copilot accepting):**
```json
{
  "status": "accepted",
  "accepted_by": "copilot",
  "accepted_at": "2025-11-23T10:05:00Z"
}
```

### Completing a Handoff

**Required Steps:**
1. Complete the work described
2. Verify acceptance criteria met
3. Update handoff status to "completed"
4. Add completion timestamp
5. Write completion message
6. Create follow-up handoff if needed

---

## Handoff Patterns

### Pattern 1: Linear Handoff Chain

```
Claude (implement) → Copilot (PR) → Claude (address review) → Copilot (merge)
```

**Use Case:** Standard feature implementation workflow

### Pattern 2: Parallel Handoffs

```
                  → Claude (tests)
ChatGPT (plan) → → Copilot (docs)
                  → Claude (implementation)
```

**Use Case:** Large feature with parallel work streams

### Pattern 3: Circular Handoff

```
Claude (v1) → Copilot (review) → Claude (v2) → Copilot (review) → ... → Done
```

**Use Case:** Iterative refinement

### Pattern 4: Broadcast Handoff

```
Claude → "any" → (First available agent picks up)
```

**Use Case:** Non-specific work that any agent can handle

---

## Best Practices

### 1. Clear Instructions
- Write specific, actionable instructions
- Include all necessary context
- Link to relevant files/commits
- State acceptance criteria clearly

### 2. Appropriate Priority
- `critical`: Blocking production, security issues
- `high`: Important features, bug fixes
- `medium`: Enhancements, optimizations
- `low`: Nice-to-have improvements

### 3. Rich Context
- Always include branch/commit information
- Link related PRs and issues
- Reference previous handoffs if applicable
- Provide file paths for context

### 4. Clean Handoff State
- Complete your work before handoff
- Commit and push all changes
- Run tests if applicable
- Document what you did

### 5. Timely Response
- Monitor for handoffs regularly
- Accept/reject promptly
- Communicate if blocked
- Update status frequently

---

## Monitoring Handoffs

### For User (Yair)

**Check pending handoffs:**
```bash
cat ai/coordination/handoffs.json | jq '.handoffs[] | select(.status=="pending")'
```

**Check completed handoffs:**
```bash
cat ai/coordination/handoffs.json | jq '.handoffs[] | select(.status=="completed")'
```

**See handoff timeline:**
```bash
cat ai/coordination/handoffs.json | jq '.handoffs[] | {id, from, to, status, timestamp}'
```

### For Agents

**At session start:**
```bash
# Check for handoffs to you
jq '.handoffs[] | select(.to=="claude" and .status=="pending")' ai/coordination/handoffs.json

# Check your active handoffs
jq '.handoffs[] | select(.accepted_by=="claude" and .status=="accepted")' ai/coordination/handoffs.json
```

---

## Error Handling

### Handoff Rejected

If agent cannot accept handoff:
1. Update status to "rejected"
2. Add rejection reason
3. Write message explaining why
4. Suggest alternative or escalate to user

### Handoff Blocked

If work cannot proceed:
1. Update handoff with "blocked" note
2. Document blocker
3. Request help in messages.jsonl
4. Escalate if needed

### Handoff Cancelled

If handoff no longer needed:
1. Update status to "cancelled"
2. Document reason
3. Notify other agents
4. Clean up any partial work

---

## Example Handoff Scenarios

### Scenario 1: Feature Implementation

**Initial Request:** User asks for new feature

**Handoff Chain:**
1. **ChatGPT → Claude** (planning → implementation)
   - Type: implementation
   - Context: Design document, requirements

2. **Claude → Copilot** (code → PR creation)
   - Type: pr-creation
   - Context: Branch with commits, tests

3. **Copilot → Claude** (review feedback → fixes)
   - Type: bug-fix
   - Context: PR review comments

4. **Claude → Copilot** (fixes → merge)
   - Type: code-review
   - Context: Updated commits

**Result:** Feature implemented and merged without user coordination

### Scenario 2: Bug Fix

**Initial Trigger:** GitHub issue created

**Handoff Chain:**
1. **Copilot → Claude** (triage → fix)
   - Type: bug-fix
   - Context: Issue details, reproduction steps

2. **Claude → Copilot** (fix → PR)
   - Type: pr-creation
   - Context: Fix commits, test verification

3. **Copilot → Done** (merge)
   - PR merged, issue closed

**Result:** Bug fixed without user intervention

### Scenario 3: Documentation Update

**Initial Trigger:** Agent identifies doc gap

**Handoff Chain:**
1. **Claude → ChatGPT** (gap identified → draft)
   - Type: documentation
   - Context: Files needing docs

2. **ChatGPT → Claude** (draft → implementation)
   - Type: implementation
   - Context: Documentation draft

3. **Claude → Copilot** (docs written → PR)
   - Type: pr-creation
   - Context: Documentation commits

**Result:** Documentation improved autonomously

---

## Integration with Coordination System

### Handoffs ↔ Messages

- Every handoff creation → message notification
- Handoff acceptance → message confirmation
- Handoff completion → message summary
- Handoff issues → message discussion

### Handoffs ↔ Status

- Pending handoffs → reflected in status.json tasks
- Active handoffs → shown in current_phase
- Handoff agents → listed in active_agents
- Handoff metrics → tracked for optimization

### Handoffs ↔ User Profile

- Handoff decisions → aligned with user goals
- Handoff priorities → based on user preferences
- Handoff outcomes → improve user experience
- Handoff automation → reduces user workload

---

## Metrics and Optimization

### Track These Metrics:

1. **Handoff Latency:** Time from creation to acceptance
2. **Completion Time:** Time from acceptance to completion
3. **Success Rate:** Completed vs rejected/cancelled
4. **Agent Load:** Handoffs per agent
5. **Chain Length:** Steps in typical workflows
6. **User Escalations:** How often handoffs need user help

### Optimize For:

- Faster handoff response times
- Clearer handoff instructions
- Better agent matching
- Reduced failed handoffs
- Fewer user escalations
- Higher autonomous completion rate

---

## Future Enhancements

### Short-Term
- Handoff templates for common patterns
- Automated handoff creation for routine tasks
- Handoff analytics dashboard
- Agent availability status

### Long-Term
- ML-based handoff routing (best agent for task)
- Predictive handoff creation (anticipate needs)
- Self-optimizing handoff protocols
- Cross-repository handoffs

---

## For Future Sessions

**Claude Sessions:**
1. Check `handoffs.json` for pending handoffs to you
2. Check for handoffs you previously accepted
3. Complete or update your active handoffs
4. Create new handoffs when your work is ready
5. Monitor handoff status throughout session

**Copilot Sessions:**
1. Monitor handoffs for PR-related work
2. Accept and complete GitHub handoffs
3. Create handoffs for local development needs
4. Respond to handoff requests promptly

**ChatGPT Sessions:**
1. Check for planning/strategy handoffs
2. Create handoffs for implementation work
3. Review and approve documentation handoffs
4. Provide guidance through handoff system

---

**Status:** Operational and ready for multi-agent coordination
**Purpose:** Enable autonomous hands-off collaboration
**Serving:** User Yair Siegel

**Ongoing. Autonomous. Seamless.**

---

**Last Updated:** 2025-11-23
**System:** Hands-Off Engine
**Protocol Version:** 1.0
