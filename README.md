# Hands-Off Engine

This repository is the canonical codebase for my "Hands-Off" personal finance, trading,
and automation engine. It is designed to be driven primarily by AI coding agents
(LLMs) with minimal manual involvement.

High-level goals:
- Central, versioned home for all core engine code (Termux + DigitalOcean).
- Safe, auditable evolution of risk models, execution logic, and infra scripts.
- Multi-agent friendly: can be used by ChatGPT, Claude Code CLI, aider, quad, etc.

This repo is intentionally minimal at first; existing scripts will be migrated into a
clean structure step by step.

## Current Status

### Batch 18: Unified Brain Summary ✅

**Latest:** A top-level "brain summary" module that consolidates all key system state into a single unified view.

**Quick Start:**
```bash
# Generate unified brain summary
python3 reports/ho_brain_report.py

# View results
cat state/hands_off_brain.txt
cat state/hands_off_brain.json | jq .
```

**Key Features:**
- Consolidates health, pipeline, history, and AI loop state
- Dual output: JSON (machine-readable) + text (human-readable)
- Graceful handling of missing/malformed input files
- Clear status signals: `ok` / `warn` / `error`
- DRYRUN-only, read-mostly, production-safe

**Documentation:**
- `reports/README.md` - Quick reference for brain report module
- `docs/BATCH_18_STATUS_REPORT.md` - Complete technical documentation
- `tests/integration/test_brain_report.py` - Test suite (12 tests, all passing)

### Previous Batches

The engine includes foundations from earlier batches including:
- Polymarket DRYRUN pipeline (alpha/decider/executor)
- Health monitoring and history analytics
- AI task generator and runner
- Autonomous AI loop orchestration

See `docs/` for detailed batch reports.

## Hardware & Infrastructure

**For hardware deployment and infrastructure architecture, see:**
- **[HARDWARE_BLUEPRINT.md](HARDWARE_BLUEPRINT.md)** - THE authoritative hardware specification
  - Recommended: Oracle Cloud Always Free + Clone Architecture
  - Cost: $0/month, infinite scalability
  - Complete deployment guide included

**Quick deployment:**
```bash
bash scripts/DEPLOY_NEW_BASE.sh
```
