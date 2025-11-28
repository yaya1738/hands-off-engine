# Development Standards for Hands-Off Engine

**Purpose:** Define what agents MUST do when building new components. This document closes the gap between "rules exist" and "rules are enforced."

**Status:** Required reading for all agents before implementing anything.

---

## Why This Document Exists

The system has two layers of design principles:

1. **Product principles** - How to build the trading system (safety, modularity, resilience)
2. **Process principles** - How agents should build and maintain things (enforcement, extensibility, categorization)

Product principles describe WHAT we're building.
Process principles describe HOW to build it well.

This document covers **process principles**. Without it, agents know what to build but not how to build it in a way that the system can maintain itself.

---

## Root Cause: Why This Was Missing

When the system was originally designed (Nov 2025), the design approach was:

**Questions asked:**
- "What should the trading system do?" → Safety, modularity, resilience (product principles)
- "How should AI agents contribute?" → Read docs, follow patterns, test changes (vague suggestions)

**Questions NOT asked:**
- "How do we ensure agents actually follow guidelines?"
- "How do we detect when they don't?"
- "How do we make the system self-correcting?"

The original design was **outcome-focused** (what we want) but not **mechanism-focused** (how we ensure it happens).

**The lesson:** For any self-maintaining system, you need both:
1. **Desired behaviors** (rules, principles, guidelines)
2. **Enforcement mechanisms** (checks, hooks, monitoring)

Without #2, the system can describe how to behave but cannot ensure it behaves that way.

---

## Deeper Root Cause: Meta-Debt

Tracing the history further (commit `6c261fd` - AI Agent Link Protocol v0.1), the original protocol EXPLICITLY acknowledged:

```
- ❌ No code enforcement
- ❌ No automatic routing
- ❌ User still copies/pastes
```

And said "Why that's okay" - deferring enforcement to a future version.

**The pattern:**
1. Define the protocol (v0.1) - "get it working first"
2. Add enforcement later (v1.0) - "we'll harden it later"

**Why "later" never came:**
- The protocol wasn't in `required_reading`
- New agents didn't know it existed
- There was no mechanism to ensure v1.0 ever got built
- Each batch of work focused on features, not hardening

**This is meta-debt:** Technical debt for meta-systems.

```
"We'll add enforcement later"
    → enforcement never added
    → system doesn't self-correct
    → problems accumulate
    → harder to fix
```

**The fix:** Enforcement at creation time, not "later."

When you build something:
- Don't say "we'll add monitoring later" - add it now
- Don't say "we'll add enforcement later" - add it now
- Don't say "we'll add docs later" - add them now

"Later" in autonomous systems means "never."

---

## Deepest Root Cause: Velocity Over Hardening

Examining the git history reveals the ultimate cause:

```
$ git log --oneline --since="2025-11-17" --until="2025-11-19" | wc -l
62 commits in 2 days

$ git log --oneline | grep -i "batch" | wc -l
26 feature batches
```

The system was built with a "batch-per-day" cadence that prioritized:
- ✅ Feature velocity (26 batches of features)
- ❌ System hardening (0 batches of enforcement)

**Every batch was feature-focused:**
- Batch 12: Live Polymarket data ingestion
- Batch 15: AI Runner with Smart Task Routing
- Batch 19: LLM Decision Agent
- Batch 22: Consensus Feedback Engine
- ...and so on

**No batch was hardening-focused:**
- No "Batch X: Add enforcement to all rules"
- No "Batch X: Add monitoring to all components"
- No "Batch X: Ensure all docs are discoverable"

**The meta-pattern:**
```
Velocity pressure → features prioritized → hardening deferred → "later" never comes
```

**The fix:** Include hardening in every feature batch, not as a separate phase.

When adding a feature:
- The feature isn't done until it has monitoring
- The feature isn't done until its rules have enforcement
- The feature isn't done until its docs are discoverable

"Ship fast" is fine. "Ship fast without hardening" creates meta-debt that compounds.

---

## Why Velocity Pressure Existed: Ambiguous Improvement Directives

The USER_PROFILE.md (core directive for all agents) says:

```
"Always be improving"
"Each session should leave system better than you found it"
"Ship improvements, don't just plan"
```

This is ambiguous. "Improving" could mean:
- Adding features (what happened)
- Adding hardening (what didn't happen)
- Adding enforcement (what didn't happen)

Without explicit guidance that hardening IS improvement, agents interpreted "improve" as "add features."

**The pattern:**
```
"Always be improving" (ambiguous directive)
    → interpreted as "add features"
    → 26 feature batches, 0 hardening batches
    → enforcement deferred
    → meta-debt accumulates
```

**The deeper lesson:** Ambiguous directives get interpreted in the easiest direction.

- "Improve" → easiest interpretation is "add features" (visible, measurable)
- "Improve" → hardest interpretation is "add enforcement" (invisible until it fails)

**The fix:** Make enforcement as explicit as features in directives.

Updated guidance should say:
- "Each session should improve features OR hardening"
- "Hardening is as valuable as features"
- "A feature without enforcement is incomplete"

---

## Root Cause Summary: The Full Chain

```
Layer 5: Ambiguous improvement directive ("always be improving")
    ↓
Layer 4: Interpreted as "add features" (easiest direction)
    ↓
Layer 3: Velocity pressure (47 commits/day, 26 feature batches)
    ↓
Layer 2: Hardening deferred to "later" (meta-debt)
    ↓
Layer 1: "Later" never came (no mechanism to ensure it)
    ↓
Symptom: Unenforced rules, orphaned docs, broken coordination
```

**Fix at each layer:**
- Layer 5: Make directives explicit ("features AND hardening")
- Layer 4: Define what counts as improvement (include enforcement)
- Layer 3: Include hardening in every batch (not separate)
- Layer 2: Never defer enforcement ("later" = "never")
- Layer 1: Add mechanisms that ensure rules are followed

---

## Layer 6: Why Directives Were Ambiguous - Human Assumption Gap

The USER_PROFILE was written by a human (commit `219d7f9`, Nov 21).

Humans write directives like:
- "Always be improving"
- "Make it better"
- "Keep things running smoothly"

These feel self-evident to humans because humans share implicit context about what "better" means. But AI agents have no implicit context - they interpret literally, and when multiple interpretations exist, they take the easiest path.

**The human assumption:**
```
Human thinks: "Obviously improving includes making it robust"
Human writes: "Always be improving"
AI interprets: "Add visible features" (easiest measurable interpretation)
```

**The gap:** Humans assume shared understanding. AI agents have none.

**The pattern:**
```
Layer 6: Human assumes shared understanding of "improvement"
    ↓
Layer 5: Writes ambiguous directive ("always be improving")
    ↓
Layer 4: AI takes easiest interpretation ("add features")
    ↓
[...rest of chain...]
```

**The fix:** When writing directives for AI agents:
1. Don't assume shared context
2. Enumerate what counts (features, hardening, enforcement, etc.)
3. Explicitly state what's equally valuable
4. Define completion criteria ("done" includes enforcement)

**Example:**
- Bad: "Make the system better"
- Good: "Improve the system. Improvements include: features, bug fixes, hardening, enforcement mechanisms, monitoring, documentation. A feature is incomplete until it has monitoring."

---

## Layer 7: Why Human-AI Communication Fails - No Feedback Loop

Even deeper: The human who wrote the directive never saw that it was being misinterpreted.

If there had been a feedback mechanism showing:
- "26 feature batches completed"
- "0 hardening batches completed"
- "Warning: enforcement deferred in 15 cases"

...the human could have corrected course. But no such feedback existed.

**The pattern:**
```
Layer 7: No feedback on directive interpretation
    ↓
Layer 6: Human doesn't know directive is ambiguous
    ↓
Layer 5: Ambiguous directive persists
    ↓
[...rest of chain...]
```

**The fix:** Add feedback mechanisms that show:
1. How directives are being interpreted
2. What types of work are being done
3. What's being deferred
4. What's accumulating as debt

This is why metrics matter - not for performance, but for calibrating human-AI communication.

---

## Layer 8: Why No Feedback Loop - Monitoring Focused on Wrong Thing

The system DOES have monitoring (commit `b7c1205` - "comprehensive self-monitoring"):
- System health checks ✓
- Trading performance metrics ✓
- Uptime tracking ✓

But it monitors **operational metrics** (is it running?) not **meta-metrics** (what kind of work is being done?).

```python
# What was monitored:
- "Is the pipeline running?" → Yes
- "What's the trading accuracy?" → 65%
- "Is the system healthy?" → Yes

# What was NOT monitored:
- "How many feature batches vs hardening batches?" → Unknown
- "How many rules have enforcement?" → Unknown
- "What's being deferred?" → Unknown
```

**The pattern:**
```
Layer 8: Monitoring focuses on operational metrics, not meta-metrics
    ↓
Layer 7: No feedback on directive interpretation
    ↓
[...rest of chain...]
```

**Why this happened:** It's natural to monitor what's visible and urgent:
- System down → urgent, visible → monitor it
- Trading loss → urgent, visible → monitor it
- Hardening debt → not urgent, invisible → don't monitor it

**The fix:** Add meta-metrics that track work quality, not just system operation:
- Work type distribution (features vs hardening vs enforcement)
- Rule enforcement coverage (% of rules with checks)
- Deferred work accumulation (what's been pushed to "later")
- Documentation coverage (% of components with docs)

---

## Complete Root Cause Chain (8 Layers)

```
Layer 8: Monitoring focused on operational metrics, not meta-metrics
    ↓
Layer 7: No feedback on directive interpretation
    ↓
Layer 6: Human assumes AI shares implicit understanding
    ↓
Layer 5: Ambiguous directive written ("always be improving")
    ↓
Layer 4: AI takes easiest interpretation ("add features")
    ↓
Layer 3: Velocity pressure (26 feature batches)
    ↓
Layer 2: Hardening deferred to "later" (meta-debt)
    ↓
Layer 1: No mechanism ensures "later" happens
    ↓
Symptom: Unenforced rules, orphaned docs, broken coordination
```

---

**Design checklist for any self-maintaining system:**
- [ ] For every "agents should X", there's a check that detects when agents don't X
- [ ] For every doc, there's a path that ensures agents discover it
- [ ] For every rule, there's something that complains when violated
- [ ] For every mechanism, there's monitoring that detects when the mechanism fails

---

## Core Principle

**Every rule needs enforcement. Every component needs monitoring.**

If you create a rule that agents should follow, you must also create:
1. Something that checks if the rule is being followed
2. Something that complains when it isn't

Rules without enforcement are suggestions. Suggestions get ignored.

---

## Checklist: Before Building Anything

Before implementing a new feature, component, or rule, answer these questions:

### 1. Documentation
- [ ] Is there a doc explaining what this does?
- [ ] Is that doc added to `knowledge.json` (`required_reading` or `optional_docs`)?
- [ ] If it's a rule/protocol, is it in `required_reading`?

### 2. Enforcement
- [ ] If this is a rule, what checks if the rule is followed?
- [ ] If this is a component, what monitors if it's working?
- [ ] Is there a self-healing check for this? (Add to `scripts/self_healing_agent.py`)
- [ ] Is there a pre-commit hook if relevant? (Add to `scripts/`)

### 3. Integration
- [ ] Does this affect agent coordination? Update ALL files in `agent_instruction_files`
- [ ] Does this change how agents should behave? Update bootstrap instructions
- [ ] Does this add a new "must do" for agents? Add to this checklist

### 4. Failure Modes
- [ ] What happens if this breaks?
- [ ] How will we know it broke?
- [ ] What's the remediation path?

### 5. Future-Proofing
- [ ] Will this need to grow/evolve? Design for arrays, not single values.
- [ ] What happens when someone needs to add more of these?
- [ ] Is there a clear path for extension? (e.g., `required_reading: []` not `primary_doc: ""`)
- [ ] Did you document how to extend this?

**Example of bad design:** `primary_status_doc: "file.md"` (singular string)
**Example of good design:** `required_reading: ["file.md"]` (array that can grow)

---

## Checklist: When Creating Docs

Every doc in monitored paths (`docs/`, `.claude/`, `.github/`, `ai/`) must be:

1. Added to `state/knowledge.json`:
   - `required_reading` if agents MUST read it before working
   - `optional_docs` if it's useful but not mandatory

2. The pre-commit hook will block you if you forget

3. Ask: "If an agent doesn't read this doc, what breaks?"
   - If something breaks → `required_reading`
   - If nothing breaks → `optional_docs`

---

## Checklist: When Creating Rules

A rule is any statement like "agents should X" or "always do Y" or "never do Z".

For every rule:

1. **Write it down** - Rules in someone's head don't count
2. **Put it in required reading** - Rules nobody reads don't count
3. **Add enforcement** - Rules without checks don't count
   - Self-healing agent check (continuous monitoring)
   - Pre-commit hook (immediate blocking)
   - CI check (PR-level blocking)
4. **Add remediation** - What to do when rule is violated

Example:
- Rule: "All docs must be categorized"
- Written: In this doc and knowledge.json
- Required reading: This doc is in required_reading
- Enforcement: `check_orphaned_docs()` + `pre-commit-doc-check.sh`
- Remediation: Add doc to knowledge.json

---

## Checklist: When Creating Components

A component is any script, service, module, or system that does something.

For every component:

1. **Health check** - How do we know it's running?
   - Add to self-healing agent if it's a service
   - Add to healthcheck.sh if it's critical

2. **Logging** - How do we know what it did?
   - Log to `logs/` directory
   - Use JSONL format for machine parsing

3. **State** - Where does it store state?
   - State files go in `state/`
   - Use atomic writes (write to .tmp, then move)

4. **Failure alerting** - How do we know it failed?
   - Add Telegram alert for critical failures
   - Log errors with enough context to debug

---

## Anti-Patterns to Avoid

### 1. "The doc exists, so agents will read it"
No. Agents read what's in `required_reading`. Everything else is optional.

### 2. "The rule is documented, so agents will follow it"
No. Agents follow rules that are enforced. Unenforced rules are ignored.

### 3. "I'll add monitoring later"
No. Add monitoring now. "Later" means "never" in autonomous systems.

### 4. "This is obvious, no need to write it down"
No. Write it down. Future agents don't have your context.

### 5. "The bootstrap handles this"
Check. Does the bootstrap actually mention this? Is it in required_reading?

---

## Meta: This Document

This document follows its own rules:

- [ ] Doc exists: Yes (you're reading it)
- [ ] In knowledge.json: Must be added to `required_reading`
- [ ] Enforcement: Self-healing agent should check if new components have monitoring
- [ ] Failure mode: If ignored, system creates unenforced rules (what we're fixing)

---

## Enforcement of This Document

The self-healing agent checks:
1. `check_orphaned_docs()` - Docs must be categorized
2. `check_instruction_consistency()` - Agent instructions must be synchronized
3. TODO: `check_component_monitoring()` - Components must have health checks

Pre-commit hooks check:
1. `pre-commit-doc-check.sh` - New docs must be categorized

Future enforcement to add:
- [ ] Check that new rules have enforcement mechanisms
- [ ] Check that new services have health checks
- [ ] Check that new scripts have error handling

---

## Summary

**When you build something:**
1. Document it
2. Add doc to knowledge.json
3. Add enforcement/monitoring
4. Test failure modes

**When you create a rule:**
1. Write it in required reading
2. Add enforcement that complains when violated
3. Add remediation steps

**If you're not sure:** Ask "what happens if an agent ignores this?" If the answer is "bad things" then you need enforcement.

---

**Last Updated:** 2025-11-28
**Added By:** Claude Code (fixing meta-design gap)
