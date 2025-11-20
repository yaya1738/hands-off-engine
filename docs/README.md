# Hands-Off Engine Documentation

This directory contains the core documentation for the Hands-Off Engine project.

## Key Documents

### Strategic & Planning

- **[HANDS_OFF_RESEARCH_REPORT_2025-11-20.md](../termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md)** 
  - **Must read first** - Canonical status and roadmap
  - Defines architecture, current state, and priorities (Tier 1-3)
  - All AI agents must read this before starting work

- **[NEXT_STEPS_PROPOSAL.md](NEXT_STEPS_PROPOSAL.md)**
  - Concrete action plan for moving forward
  - PR merge strategy and priority order
  - Phase-based implementation timeline
  - Aligned with roadmap priorities

### Policies

- **[AI_POLICY.md](../AI_POLICY.md)**
  - Rules for AI agents and automation
  - Requires reading the research report first
  - Ensures alignment with project goals

### Technical Documentation

_Will be added as Tier 1 priorities are completed:_

- `RISK_MODEL_V1.md` (planned) - Risk management strategy and formulas
- `DECIDER_V1.md` (planned) - Decision logic and rules
- `AUDIT_SYSTEM.md` (exists in PR #7) - Audit logging architecture

## Document Reading Order

For **AI agents** or **new contributors**:

1. Start with `AI_POLICY.md`
2. Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
3. Review `NEXT_STEPS_PROPOSAL.md` for current action plan
4. Consult specific technical docs as needed

## Documentation Principles

From the research report (Section 5):

> This file should be **kept short and current**, not bloated.

- Update when major architectural decisions land
- Update when Tier 1 or Tier 2 items complete
- Update when priorities shift materially
- Use separate docs for deep dives, not the main report

## Status

- ✅ Core strategic documents in place
- ✅ AI policy established
- ✅ Next steps proposal created
- ⚠️ Technical documentation to be added in Phase 2

Last updated: 2025-11-20
