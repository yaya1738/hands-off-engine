# System Assumptions

**Purpose:** Document implicit assumptions that components make about each other and the environment. Hidden assumptions cause novel failures when violated.

**Created:** Layer 71 fix in root cause analysis (see DEVELOPMENT_STANDARDS.md)

---

## Why This Document Exists

From Layer 51-53 of the root cause analysis:

> Components make assumptions about each other:
> - A assumes B responds in <100ms
> - B assumes A sends valid data
> - Neither assumption is explicit
> - When both assumptions hold: works
> - When one breaks: novel failure

**Hidden assumptions are invisible until violated.**

This document makes them visible.

---

## Environment Assumptions

### Operating System
- **Assumption:** Linux environment (Ubuntu/Debian)
- **Violated when:** Running on Mac/Windows without compatibility layer
- **Impact:** Scripts may fail, paths wrong
- **Mitigation:** Check OS on startup, warn if incompatible

### File System
- **Assumption:** File system is writable
- **Violated when:** Disk full, permissions wrong
- **Impact:** State not saved, logs not written
- **Mitigation:** `check_disk_space()` in self-healing agent

### Network
- **Assumption:** Internet connectivity available
- **Violated when:** Network down, DNS fails
- **Impact:** API calls fail, git operations fail
- **Mitigation:** Retry with backoff, local caching

### Time
- **Assumption:** System clock is accurate
- **Violated when:** NTP not running, clock drift
- **Impact:** Scheduled tasks run at wrong time, logs confusing
- **Mitigation:** Use relative times where possible

---

## Infrastructure Assumptions

### Git
- **Assumption:** Git is installed and configured
- **Violated when:** Git missing, auth not configured
- **Impact:** Version control fails, sync breaks
- **Mitigation:** `check_git_locks()` in self-healing, auth check on startup

### Cron
- **Assumption:** Cron daemon running, jobs execute on schedule
- **Violated when:** Cron disabled, system overloaded
- **Impact:** Autonomous operations don't run
- **Mitigation:** `check_cron_job()` in self-healing agent

### Python
- **Assumption:** Python 3.8+ available with required packages
- **Violated when:** Wrong Python version, packages not installed
- **Impact:** Scripts fail
- **Mitigation:** requirements.txt, version check on startup

---

## Service Assumptions

### Telegram Bot
- **Assumption:** Bot token valid, Telegram API available
- **Violated when:** Token revoked, API down, rate limited
- **Impact:** Alerts not delivered
- **Mitigation:** Fallback to log file, retry logic

### Polymarket API
- **Assumption:** API available, response format stable
- **Violated when:** API changes, rate limited, down
- **Impact:** Trading signals stale
- **Mitigation:** Caching, staleness checks, fallback to cached data

### LLM APIs (Claude, OpenAI)
- **Assumption:** API keys valid, APIs available
- **Violated when:** Keys expired, quota exceeded, API down
- **Impact:** LLM-driven decisions fail
- **Mitigation:** Backend fallback (`backend_selector.py`), graceful degradation

---

## Component Interface Assumptions

### Signal Pipeline → Executor
- **Assumption:** Signals are in expected JSON format
- **Assumption:** Signal timestamps are recent (<1 hour old)
- **Assumption:** Signal confidence is 0-1 float
- **Violated when:** Format changes, stale signals passed
- **Impact:** Executor acts on bad data
- **Mitigation:** Schema validation, staleness check

### Self-Healing Agent → State Files
- **Assumption:** State files are valid JSON
- **Assumption:** State files exist where expected
- **Violated when:** Corruption, files deleted
- **Impact:** Health checks fail
- **Mitigation:** JSON validation, create if missing

### AI Agents → knowledge.json
- **Assumption:** knowledge.json exists and is valid
- **Assumption:** Paths in required_reading are valid
- **Violated when:** File deleted, paths stale
- **Impact:** Agents don't read required docs
- **Mitigation:** `check_orphaned_docs()` in self-healing

---

## Process Assumptions

### Autonomous Operation
- **Assumption:** System runs without human intervention
- **Violated when:** Human changes config mid-run, manual interference
- **Impact:** State inconsistency
- **Mitigation:** Document expected autonomous behavior, lock files

### Multi-Agent Coordination
- **Assumption:** Only one agent writes to a file at a time
- **Violated when:** Race conditions, concurrent agents
- **Impact:** Data corruption, lost writes
- **Mitigation:** Lock files, atomic writes

### Session Continuity
- **Assumption:** State persists between Claude Code sessions
- **Violated when:** State files not committed, lost
- **Impact:** Context lost, decisions repeated
- **Mitigation:** Commit state changes, document in session logs

---

## Adding New Assumptions

When you discover a hidden assumption (usually via failure):

1. **Document it here** with:
   - What the assumption is
   - When it's violated
   - What the impact is
   - What mitigation exists (or should be added)

2. **Add mitigation** if none exists:
   - Self-healing check
   - Validation on input
   - Fallback behavior

3. **Consider: Is this assumption necessary?**
   - Can the design be changed to not require it?
   - Can it fail gracefully instead of hard?

---

## Assumption Debt

**Current known assumption debt (things we assume but don't validate):**

- [ ] System timezone is UTC
- [ ] Git remote is accessible (no offline mode)
- [ ] All Python imports succeed (no graceful degradation)
- [ ] Config files are human-readable (no encryption)
- [ ] Single-instance operation (no clustering)

Add to this list when you notice an unvalidated assumption.

---

**Last Updated:** 2025-11-28
**Created By:** Layer 71 of root cause analysis
