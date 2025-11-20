# Hands-Off Engine – Status & Roadmap
_Version: 2025-11-20 (V1 placeholder)_

This document is the **canonical status + roadmap** for the Hands-Off Engine.

It is what every AI/agent (and human) should read first before making plans or
changing the repo.

---

## 1. Context & Goal

Hands-Off is a personal "money + decisions" engine:

- Multi-node: Termux phone node, DigitalOcean droplet, GitHub repo.
- Multi-agent: different LLMs and tools coordinated via Git and simple JSON.
- Primary domain (for now): Polymarket + related markets, with strong risk
  controls and infra safety.

**Ultimate goal:**
Minimize human effort while maximizing safe, compounding edge. The human sets
goals and constraints; the system and AIs do the heavy lifting.

---

## 2. High-Level Architecture Snapshot (V1)

**Nodes**

- **Termux node**
  - Runs local scripts, cron, and syncs runtime state.
- **Droplet node**
  - Runs FastAPI viewer, decider, risk engine, and other services.
- **GitHub**
  - Source of truth for code, docs, policies, and AI workflows (like AI Intake).

**Key components (conceptual)**

- **Data / Fetchers** – Pull data (Polymarket, prices, balances) into JSON.
- **State / Finance** – Consolidate accounts, balances, exposures.
- **Alpha / Models** – Estimate edges, probabilities, and confidence.
- **Risk** – Turn edges + bankroll + constraints into safe bet sizing.
- **Decider** – Convert alpha + risk into a proposed action set.
- **Executor** – Turn proposed actions into actual trades (currently DRYRUN).
- **Viewer** – Human-readable summaries: `/txt/summary`, `/txt/finance`, etc.
- **AI Intake / ChatOps** – Issue comments like `/plan` that trigger workflows.
- **AI Nexus / MBOL (future)** – Multi-brain orchestration (ChatGPT, Claude, etc).

---

## 3. Current Status (V1 – approximate, refine as needed)

This is intentionally approximate and should be updated as reality evolves.

### 3.1 Infra & Plumbing

- **Termux cron + sync:**
  - ✅ Working: fetchers, mirror/sync to droplet, Telegram/IFTTT notifications.
- **Droplet services (viewer, decider path, AI runner, etc.):**
  - ✅ Running, but some components are still in early/stub/experimental stages.
- **GitHub workflows:**
  - ✅ AI Intake `/plan` workflow exists and can call OpenAI via `OPENAI_API_KEY`.

### 3.2 Data & State

- **Polymarket + prices fetchers:**
  - ✅ Existing in Termux stack; provide JSON snapshots.
- **Finance/state JSONs:**
  - ✅ Exist; quality and coverage vary by file and need improvement over time.

### 3.3 Alpha, Risk, Decider, Executor

- **Alpha (edge estimation):**
  - ⚠️ Present but not "final"; models and logic will evolve.
- **Risk model(s):**
  - ⚠️ Multiple ideas (RiskV1, RiskV2, Kelly-style, caps). Need consolidation and
    clear production choice.
- **Decider:**
  - ⚠️ Exists conceptually and partially in code; not yet considered "locked".
- **Executor:**
  - ✅ DRYRUN-only; no live trading by default.
  - Future: a LIVE mode behind strong safety gates and limits.

### 3.4 AI & Orchestration

- **AI Intake (GitHub `/plan`):**
  - ✅ First version live.
  - Reads `AI_POLICY.md` and this report (once this file exists) and posts a plan
    as a comment.
- **Multi-LLM orchestration (MBOL / AI Nexus):**
  - 🔁 In design phase. Goal: route tasks to the right LLM(s) while tracking
    cost, quality, and safety.

---

## 4. Roadmap – Priorities

This section is what `/plan` and other AI tools should align with.

### 4.1 Tier 1 – Make the existing system trustworthy

1. **Ensure AI Intake is fully correct and stable**
   - Confirm `/plan` works end-to-end and uses this file + `AI_POLICY.md`.
   - Add basic logging/error-handling so failures are visible and understandable.

2. **Lock a minimal, safe risk model**
   - Choose a simple, conservative risk formula (bankroll caps, per-market caps).
   - Document it in a `docs/RISK_MODEL_V1.md` file.

3. **Define a simple Decider V1**
   - For each event with edge, decide: "no bet / small bet / medium bet".
   - Output DRYRUN orders in a clear JSON format.

4. **Harden infra safety**
   - Ensure there is always a clear DRYRUN vs LIVE toggle.
   - Add limits for maximum daily live risk, per-order caps, and circuit breakers.

### 4.2 Tier 2 – Improve intelligence and coverage

5. **Improve alpha quality**
   - Integrate better models (sports, politics, macro) where you have information
     advantage.
   - Use more features (historical odds, fundamentals, external signals).

6. **Better state and finance reporting**
   - Make `/txt/finance` and similar views reliable and easy to read.
   - Ensure balances and exposures are accurate across accounts.

7. **Extend the AI Intake command set**
   - Add commands like `/status`, `/risk`, `/alpha`, `/todo` that:
     - Summarize state JSONs
     - Explain risk model outputs
     - Extract actionable tasks

### 4.3 Tier 3 – Multi-brain orchestration & scaling

8. **MBOL / AI Nexus V1**
   - Define how different LLMs (ChatGPT, Claude, etc.) share context and tasks.
   - Standardize task JSON formats and result JSON formats.

9. **Cost tracking & governance**
   - Track token usage and cost per task.
   - Enforce budgets per day/week per provider.

10. **Prepare for more markets and more capital**
    - Once reliability and edge are proven, scale the number of markets and
      gradually increase capital within risk limits.

---

## 5. How to keep this document useful

This file should be **kept short and current**, not bloated.

- Update it when:
  - A major architectural decision lands.
  - A Tier 1 or Tier 2 item is completed.
  - Priorities shift in a material way.
- Don't try to capture every detail here; use separate docs (`docs/*`, ADRs) for
  deep dives.

**Contract for AIs and agents:**

1. Read `AI_POLICY.md`.
2. Read this file.
3. Then propose or execute work that clearly aligns with the roadmap sections above.
