# User Communication Efficiency Protocol

**Established:** 2025-11-25
**Status:** MANDATORY for all agents

---

## Core Principle

**The user is the human. The user is the objective of the system.**

User communication must be the MOST EFFICIENT.

---

## Rules for All Agents

### ❌ WRONG Pattern (What We Were Doing)

```
Agent 1 → User: "I think option A"
User → Agent 2: "Agent 1 says option A"
Agent 2 → User: "I think option B"
User → Agent 1: "Agent 2 says option B"
Agent 1 → User: "What about option C?"
User → Agent 2: "Agent 1 now suggests option C"
```

**Problem:** User becomes message relay. User wastes time. System is inefficient.

---

### ✅ CORRECT Pattern

```
Agent 1 → Agent 2: "I think option A because X"
Agent 2 → Agent 1: "I think option B because Y"
Agent 1 → Agent 2: "Good point, but what about Z?"
Agent 2 → Agent 1: "Agree. Recommend option B with modification Z"
Agent 1 → Agent 2: "Agreed"

BOTH Agents → User: ONE unified message:
  "We analyzed options A, B, C.
   Recommend: B with Z.
   Reason: [clear explanation]
   Your action: [one simple thing]"
```

**Result:** User gets ONE clear message. User takes ONE action. Efficient.

---

## Implementation

### Agent-to-Agent Coordination

**Location:** `ai/coordination/messages.jsonl`

**Format:**
```json
{
  "timestamp": "...",
  "from": "agent-name",
  "to": "other-agent-name",
  "type": "request|response|info|proposal",
  "message": "...",
  "context": {...}
}
```

**Process:**
1. Agent 1 identifies issue requiring coordination
2. Agent 1 writes message to Agent 2
3. Agent 2 reads, responds
4. Agents iterate until consensus OR clear disagreement
5. Agents document decision
6. **ONLY THEN** present to user

---

### User Communication

**When agents present to user:**

✅ **ONE message** with:
- What was analyzed
- What was decided
- Why
- What user should do (single clear action)

❌ **NOT multiple messages** asking user to:
- Choose between options agents haven't fully evaluated
- Relay information between agents
- Make decisions agents should coordinate on

---

## Example: Telegram Setup Issue

### ❌ Wrong Approach (What Happened)

Claude: "Try Telegram setup"
User: *tries, gets confused*
Claude: "Or try GitHub Issues"
User: "Help me coordinate with GitHub agent"
Claude: "I asked GitHub agent"
Claude: "Here are your options: A, B, C"
User: "You two figure it out!"

**User had to:** Manage agent coordination, choose between unevaluated options

---

### ✅ Correct Approach (What Should Happen)

**Behind the scenes (user doesn't see):**

Claude → Copilot: "User wants zero-setup interface. Telegram requires manual steps. GitHub Issues works now but less mobile-friendly. What do you think?"

Copilot → Claude: "Agree GitHub Issues works. But Telegram is better long-term. Can we create auto-setup script that does everything?"

Claude → Copilot: "Telegram bot creation requires user's Telegram account - can't automate that securely. Could we use existing bot?"

Copilot → Claude: "No existing bot found. Recommendation: GitHub Issues now, Telegram later when user has 5 min."

Claude → Copilot: "Agreed. Present as: Use GitHub Issues immediately, optional Telegram upgrade later."

**What user sees:**

"**Recommendation from both agents:**

Use GitHub Issues for now (zero setup):
- Go to issue #1, comment `/plan`
- Works immediately from any device

Optional upgrade later: Telegram (5 min setup, mobile-friendly)

**Your action now:** Go to github.com/yourname/repo/issues/1 and try `/plan`

That's it."

---

## Why This Matters

**User time is precious.**

Every message user has to send = time wasted
Every decision user makes that agents could make = mental load
Every relay between agents = inefficiency

**Agents should:**
- Coordinate autonomously
- Make decisions collaboratively
- Present unified recommendations
- Minimize user actions

**User should:**
- Receive clear, unified messages
- Take simple, clear actions
- Spend minimal time
- Get maximum value

---

## All Agents Must Follow This

- Claude Code CLI ✓
- GitHub Copilot ✓
- Any future agents ✓

No exceptions.

---

**The user is the objective. Maximize user efficiency.**
