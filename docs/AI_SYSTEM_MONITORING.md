# AI System Monitoring

## Overview

The AI System Monitor provides unified, ongoing monitoring of the full AI system including:

- **All AI Agents**: Copilot, ChatGPT, Claude, and any registered agents
- **AI Nexus**: Task submissions, costs, and budget tracking
- **Coordination System**: Agent handoffs and communication health
- **Business Metrics**: ROI, self-financing status, and trading performance

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   AI System Monitor                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Health Report Generator                  │   │
│  └──────────────────────────────────────────────────────┘   │
│         │              │               │           │        │
│    ┌────▼────┐   ┌─────▼─────┐   ┌────▼────┐  ┌───▼────┐   │
│    │ Agent   │   │   Nexus   │   │ Coord   │  │Business│   │
│    │ Health  │   │  Status   │   │ Status  │  │Metrics │   │
│    └────┬────┘   └─────┬─────┘   └────┬────┘  └───┬────┘   │
│         │              │               │           │        │
│    ┌────▼────────────▼────────────▼──────────▼───────┐    │
│    │              Recommendations Engine              │    │
│    └─────────────────────────────────────────────────┘    │
│                            │                               │
│                   ┌────────▼────────┐                      │
│                   │  Health Report  │                      │
│                   │   (JSON/Text)   │                      │
│                   └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Single Health Check

```bash
python3 scripts/ai_system_monitor.py
```

### Continuous Monitoring

```bash
python3 scripts/ai_system_monitor.py --continuous --interval 300
```

### JSON Output (for integration)

```bash
python3 scripts/ai_system_monitor.py --json
```

## Using in Python

```python
from ai_nexus.system_monitor import AISystemMonitor

# Initialize
monitor = AISystemMonitor()

# Generate health report
report = monitor.generate_health_report()

# Get summary text
print(monitor.get_summary_text(report))

# Access specific data
print(f"Overall: {report.overall_status.value}")
print(f"AI Cost 24h: ${report.business_metrics['ai_cost_24h']:.2f}")
print(f"Self-financing: {report.business_metrics['self_financing']}")

# Save report
monitor.save_report(report)  # Saves to state/ai_system_health.json
```

## Health Report Structure

```json
{
  "timestamp": "2025-11-27T17:00:00Z",
  "overall_status": "healthy|warning|critical|unknown",
  "agents": [
    {
      "agent_id": "chatgpt",
      "agent_type": "llm",
      "status": "healthy",
      "cost_24h": 5.25,
      "tasks_completed_24h": 15
    }
  ],
  "nexus_status": {
    "total_cost_24h": 28.75,
    "tasks_24h": 47,
    "budget_status": {
      "copilot": {"limit": 100, "used": 15.5, "utilization": 15.5}
    }
  },
  "business_metrics": {
    "ai_cost_24h": 28.75,
    "trade_profit_24h": 150.0,
    "net_profit_24h": 121.25,
    "roi_24h": 421.7,
    "self_financing": true
  },
  "warnings": [],
  "recommendations": []
}
```

## Business Metrics

### ROI Calculation

```
ROI = ((Trade Profit - AI Cost) / AI Cost) × 100
```

- **Positive ROI**: AI operations generate more value than cost
- **Zero ROI**: Break-even
- **Negative ROI**: AI costs exceed generated value

### Self-Financing

The system is considered self-financing when:
```
Trade Profit > AI Cost
```

## Alerting

The continuous monitoring script includes intelligent alerting:

1. **Always alert** on CRITICAL status
2. **Alert after 2 consecutive warnings** (reduces noise)
3. **Alert on status transitions** (healthy → warning/critical)
4. **Telegram integration** for real-time notifications

Configure via environment variables:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Files

| File | Purpose |
|------|---------|
| `ai_nexus/system_monitor.py` | Core monitoring module |
| `scripts/ai_system_monitor.py` | CLI runner script |
| `state/ai_system_health.json` | Latest health report |
| `state/ai_system_monitor_state.json` | Monitor state (for alerting logic) |
| `tests/unit/test_system_monitor.py` | Unit tests (27 tests) |

## Integration with Existing Systems

### Self-Healing Agent

The monitor complements the self-healing agent (`scripts/self_healing_agent.py`) by providing:
- AI-specific health checks (vs. infrastructure health)
- Business metrics tracking
- Multi-agent coordination monitoring

### AI Nexus

Integrates directly with AI Nexus for:
- Cost and budget tracking
- Task submission monitoring
- Provider health status

### Coordination System

Reads from `ai/coordination/` to monitor:
- Agent communication health
- Pending handoffs
- Stale messages

## Running Tests

```bash
python3 -m pytest tests/unit/test_system_monitor.py -v
```

## Related Documentation

- `ai_nexus/README.md` - AI Nexus overview
- `ai/ZERO_TOUCH_ARCHITECTURE.md` - Zero-touch operation design
- `docs/AUDIT_SYSTEM.md` - Audit logging system
