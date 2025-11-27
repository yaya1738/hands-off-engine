# Hands-Off Engine

> **For Yair Siegel** — A fully autonomous, self-improving system where money grows itself, software improves itself, and hardware manages itself — all in harmony.

## Quick Links

| Document | Purpose |
|----------|---------|
| [Autonomous Harmony Engine](docs/AUTONOMOUS_HARMONY_ENGINE.md) | Unified self-improvement architecture |
| [Risk Model V1](docs/RISK_MODEL_V1.md) | Trading risk parameters |
| [User Interface](USER_INTERFACE.md) | Telegram-only user protocol |
| [Status & Roadmap](termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md) | Current status and next steps |

## The Three Autonomous Domains

```
┌─────────────────────────────────────────────────────────────────┐
│                HANDS-OFF ENGINE - Autonomous Harmony            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  💰 MONEY           🔧 SOFTWARE         💻 HARDWARE             │
│  Self-Growth        Self-Improvement    Self-Management         │
│                                                                 │
│  • Alpha learning   • Self-healing      • Auto-scaling          │
│  • Position sizing  • Code quality      • Cost optimization     │
│  • Phase progression• Bug detection     • Resource monitoring   │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                    🎯 HARMONY ORCHESTRATOR                      │
│          Coordinates all domains for maximum benefit            │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

1. **Money grows itself**: Trading alpha improves through outcome learning, positions auto-size, capital compounds
2. **Software improves itself**: Bugs auto-fix, code quality increases, performance optimizes
3. **Hardware manages itself**: Resources scale, costs minimize, uptime maximizes

**Your involvement**: ~15 minutes per week via Telegram

## Status & Roadmap

See `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
for the current status and next steps.

### For any AI / agent working on this repo

Before doing anything substantial, the AI/agent MUST:

1. Read `AI_POLICY.md`
2. Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
3. Follow the roadmap and constraints described there

This repository is the canonical codebase for the "Hands-Off" personal finance, trading,
and automation engine. It is designed to be driven primarily by AI coding agents
(LLMs) with minimal manual involvement.

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Harmony Orchestrator | `scripts/harmony_orchestrator.py` | Coordinates all autonomous domains |
| Self-Improvement Engine | `scripts/self_improvement_engine.py` | Software self-improvement |
| Alpha Self-Learning | `alpha/alpha_self_learning.py` | Trading strategy learning |
| Self-Healing Agent | `scripts/self_healing_agent.py` | Auto-fixes common issues |
| Coordination Agent | `scripts/coordination_agent.py` | AI-to-AI coordination |
| AI Nexus | `ai_nexus/nexus.py` | Multi-AI orchestration |

## Running the System

```bash
# Run harmony orchestrator (coordinates all domains)
python scripts/harmony_orchestrator.py --once

# Run self-improvement scan
python scripts/self_improvement_engine.py

# Run alpha learning cycle
python alpha/alpha_self_learning.py

# Run tests
python tests/unit/test_autonomous_harmony.py
```

## Architecture Goals

- Central, versioned home for all core engine code (Termux + DigitalOcean)
- Safe, auditable evolution of risk models, execution logic, and infra scripts
- Multi-agent friendly: can be used by ChatGPT, Claude Code CLI, aider, quad, etc.
- Fully autonomous: system maintains and improves itself without human intervention