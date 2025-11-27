# Autonomous Hardware Monitoring Integration

## Overview

This document describes the integration between two hardware monitoring implementations:

1. **Self-Healing Agent** (`scripts/self_healing_agent.py`) - Simple, lightweight monitoring
2. **Unified Autonomous System** (Claude's branch) - Comprehensive, business-integrated system

## Claude's Autonomous Hardware Monitoring Branch

Branch: `claude/autonomous-hardware-monitoring-018Zmksp8vodwHm5wWUFiWUi`

### Components

#### `hardware/` Module
| File | Purpose |
|------|---------|
| `autonomous_hardware_monitor.py` | Main monitoring daemon |
| `hardware_analyzer.py` | Health assessment, anomaly detection, trend analysis |
| `hardware_collector.py` | Real-time system metrics collection |
| `hardware_decision_engine.py` | AI-driven decision making |
| `hardware_kernel.py` | Persistent learning from patterns |
| `trading_protection.py` | Live trading protection layer |
| `hardware_dashboard.py` | CLI dashboard for status |
| `hardware_audit.py` | Full audit trail integration |
| `hardware_types.py` | Data models for metrics/health/decisions |

#### `infrastructure/` Module
| File | Purpose |
|------|---------|
| `auto_provisioner.py` | Automatic server upgrades and provisioning |
| `autonomous_infra_manager.py` | Continuous infrastructure management |
| `cloud_providers.py` | DigitalOcean + AWS API integrations |
| `infra_types.py` | Infrastructure data models |

#### `autonomous/` Module
| File | Purpose |
|------|---------|
| `unified_system.py` | Master controller combining all components |

### Key Features

1. **Hardware Monitoring**
   - CPU, memory, disk, network, thermal metrics
   - Adaptive thresholds based on learned baselines
   - Anomaly detection and trend analysis

2. **Autonomous Decision Making**
   - Auto-execute emergency decisions (OOM prevention, thermal mitigation)
   - Budget-aware scaling decisions
   - Auto-approve changes within budget
   - Queue risky decisions for Telegram approval

3. **Trading Protection**
   - Live money protection layer
   - Emergency halt capability
   - Automatic throttling during hardware issues
   - Maintenance window scheduling

4. **Infrastructure Management**
   - DigitalOcean and AWS cloud providers
   - Automatic server upgrades
   - Horizontal scaling during critical situations
   - Budget enforcement

## Self-Healing Agent (This PR)

The `scripts/self_healing_agent.py` provides a simpler, lightweight alternative:

### Features Added
- CPU/Memory monitoring via `top` and `free` commands
- DigitalOcean API integration for droplet resize
- Runaway process detection and auto-kill
- Resource history tracking
- Telegram alerts

### Configuration
- `config/resource_limits.json` - Thresholds and settings
- Environment variables: `DIGITALOCEAN_API_TOKEN`, `DIGITALOCEAN_DROPLET_ID`

## Recommendation

**Merge Claude's branch** for the full Unified Autonomous System. It provides:

1. ✅ Comprehensive hardware monitoring with learning
2. ✅ Multi-cloud provider support (DO + AWS)
3. ✅ Business process integration (approval queue)
4. ✅ Trading protection (always-on)
5. ✅ Systemd service for daemon operation
6. ✅ Full audit trail

The self-healing agent changes in this PR are a simpler subset suitable for basic monitoring, but Claude's system is what's needed for the "hands-off" autonomous operation described by the user.

## To Merge Claude's Branch

```bash
git fetch origin
git checkout main
git merge origin/claude/autonomous-hardware-monitoring-018Zmksp8vodwHm5wWUFiWUi
```

## Running the Unified System

Once merged:

```bash
# Dry run (testing)
python -m autonomous.unified_system --budget 500 --dry-run

# Live operation
python -m autonomous.unified_system --budget 500

# Install as systemd service
sudo ./scripts/install_autonomous.sh
```

## Required Environment Variables

```bash
# DigitalOcean (primary)
export DO_API_TOKEN="your-digitalocean-token"

# OR AWS (backup)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Telegram notifications (optional)
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

## Autonomous Behavior

| Action | Trigger | Approval Needed? |
|--------|---------|------------------|
| Upgrade server | Health < 70% | Auto if < $50/mo increase |
| Provision new server | Critical health | Auto (emergency) |
| Scale horizontally | Persistent critical | Auto if within budget |
| Trading protection | Any risk detected | Always auto |
| Alerts | Any threshold breach | Never (just logs) |

**User intervention: NEVER required for normal operations.**
