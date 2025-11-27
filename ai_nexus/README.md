# AI Nexus - Multi-Brain Orchestration System

The AI Nexus is the central orchestration layer that coordinates multiple AI agents (Copilot, ChatGPT, Claude, etc.) with full audit trail, cost tracking, and financial ledger for self-financing capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Nexus                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Copilot    │  │   ChatGPT    │  │    Claude    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│               ┌────────────▼────────────┐                    │
│               │   Task Router &         │                    │
│               │   Budget Manager        │                    │
│               └────────────┬────────────┘                    │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐             │
│         │                                      │             │
│  ┌──────▼──────┐                      ┌───────▼──────┐      │
│  │ Audit Logger│                      │Action Ledger │      │
│  │  (events)   │                      │  (finances)  │      │
│  └─────────────┘                      └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Multi-AI Orchestration
- **Intelligent Routing**: Automatically selects the best AI provider based on task type, cost, and availability
- **Budget Management**: Enforces daily spending limits per provider
- **Cost Tracking**: Real-time monitoring of AI operation costs

### 2. Complete Audit Trail
- **Every Action Logged**: All AI operations tracked through audit system
- **Full Transparency**: Session-based grouping for complete traceability
- **Error Tracking**: Failures and exceptions captured with context

### 3. Financial Ledger
- **Immutable Record**: All costs and revenues tracked in append-only ledger
- **ROI Calculation**: Track return on AI investment
- **Self-Financing**: Monitor whether AI operations are profitable

### 4. Self-Improvement
- **Performance Metrics**: Track which AI providers perform best
- **Cost Optimization**: Identify and eliminate wasteful operations
- **Adaptive Budgets**: Adjust spending based on ROI

## Components

### AINexus (`nexus.py`)
Central orchestrator that:
- Routes tasks to AI providers
- Manages budgets and spending
- Records all operations
- Tracks performance metrics

### ActionLedger (`ledger.py`)
Financial tracking system that:
- Records all costs and revenues
- Calculates daily/weekly/monthly summaries
- Computes ROI
- Enables self-financing analysis

### Copilot Integration (`copilot_integration.py`)
GitHub Copilot wrapper that:
- Routes all Copilot actions through AI Nexus
- Tracks code generation costs
- Monitors code review expenses
- Reports session summaries

### System Monitor (`system_monitor.py`)
Unified monitoring system that:
- Monitors all AI agents (Copilot, ChatGPT, Claude)
- Tracks AI Nexus task submissions and costs
- Checks coordination system health
- Calculates business-aligned metrics (ROI, self-financing)
- Generates actionable recommendations

## Usage

### Basic Task Submission

```python
from ai_nexus import AINexus, AITask, TaskPriority

# Initialize nexus
nexus = AINexus()

# Submit a task
task = AITask(
    task_id="task123",
    task_type="planning",
    description="Generate risk model roadmap",
    priority=TaskPriority.HIGH,
    max_cost=5.0
)

task_id = nexus.submit_task(task)
```

### Track Copilot Actions

```python
from ai_nexus.copilot_integration import CopilotNexusWrapper

# Initialize wrapper
wrapper = CopilotNexusWrapper()

# Log code generation
wrapper.log_code_generation(
    files_changed=3,
    lines_added=150,
    lines_deleted=20,
    cost=2.50
)

# Get session summary
summary = wrapper.get_session_summary()
print(f"Budget used: ${summary['budget']['used']:.2f}")
```

### Financial Reporting

```python
from ai_nexus import ActionLedger

# Initialize ledger
ledger = ActionLedger()

# Get daily summary
summary = ledger.get_daily_summary()
print(f"Profit: ${summary['total_profit']:.2f}")

# Calculate ROI
roi = ledger.calculate_roi("2025-11-01", "2025-11-30")
print(f"Monthly ROI: {roi:.1f}%")
```

### Query Operations

```bash
# View all AI Nexus operations
python3 audit/audit_viewer.py --component ai_nexus

# View ledger entries
cat logs/ledger/ledger_2025-11-20.jsonl | python3 -m json.tool

# Check budget status
python3 -c "from ai_nexus import AINexus; n = AINexus(); print(n.get_budget_status())"
```

### Monitor System Health

```bash
# Run single health check
python3 scripts/ai_system_monitor.py

# Run continuous monitoring (5 min interval)
python3 scripts/ai_system_monitor.py --continuous

# Get JSON output for integration
python3 scripts/ai_system_monitor.py --json
```

### Using the System Monitor in Python

```python
from ai_nexus.system_monitor import AISystemMonitor

# Initialize monitor
monitor = AISystemMonitor()

# Generate health report
report = monitor.generate_health_report()

# Get human-readable summary
print(monitor.get_summary_text(report))

# Save report to file
monitor.save_report(report)

# Access specific data
print(f"Overall: {report.overall_status.value}")
print(f"Agents: {len(report.agents)}")
print(f"Cost 24h: ${report.business_metrics['ai_cost_24h']:.2f}")
print(f"Self-financing: {report.business_metrics['self_financing']}")
```

## Budget Limits

Default daily limits (configurable):
- **Copilot**: $100/day
- **ChatGPT**: $50/day
- **Claude**: $50/day
- **OpenAI**: $50/day

## Storage

### Audit Logs
- Location: `logs/audit/audit_YYYY-MM-DD.jsonl`
- Format: JSON Lines (one event per line)
- Retention: Indefinite (manually archive)

### Action Ledger
- Location: `logs/ledger/ledger_YYYY-MM-DD.jsonl`
- Format: JSON Lines (one entry per line)
- Retention: Indefinite (for financial records)

### AI Nexus State
- Location: `logs/ai_nexus/nexus_state.json`
- Format: JSON
- Contents: Daily costs, task queue, configuration

## Self-Financing Capabilities

The AI Nexus enables the system to become self-financing by:

1. **Tracking All Costs**: Every AI operation cost is recorded
2. **Attributing Revenue**: Trading profits linked to AI decisions
3. **Calculating ROI**: Measure whether AI is profitable
4. **Optimizing Spend**: Identify and eliminate wasteful AI usage
5. **Adaptive Budgets**: Increase AI spending when ROI is positive

### Example Self-Financing Workflow

```python
# 1. AI generates trading idea (cost: $2)
task_id = nexus.submit_task(AITask(...))

# 2. Trade executes and profits (revenue: $50)
ledger.record_trade(market="...", profit=50.0)

# 3. Calculate net impact
summary = ledger.get_daily_summary()
print(f"Net profit: ${summary['total_profit']:.2f}")  # $48

# 4. If profitable, increase AI budget for tomorrow
if summary['total_profit'] > 0:
    nexus.budget_limits['copilot'] *= 1.1  # 10% increase
```

## Integration with Existing Systems

### AI Intake Handler
The AI Intake handler (`ai/ai_intake_handler.py`) already routes through the audit system. To integrate with AI Nexus:

```python
from ai_nexus.copilot_integration import CopilotNexusWrapper

wrapper = CopilotNexusWrapper()

# Log AI Intake operation
wrapper.start_task(
    task_type="plan_generation",
    description="/plan command execution",
    priority=TaskPriority.HIGH
)
```

### Trading System
Connect trading operations to the ledger:

```python
from ai_nexus import ActionLedger

ledger = ActionLedger()

# After trade execution
ledger.record_trade(
    market="btc_100k_eoy",
    side="BUY",
    size=100.0,
    price=0.30,
    profit=15.0
)
```

### Decision Engine
Track decision-making costs:

```python
from ai_nexus import ActionLedger

ledger = ActionLedger()

# After decision made
ledger.record_decision(
    decision_type="bet_sizing",
    cost=0.10,  # AI cost to make decision
    expected_value=50.0  # Expected profit
)
```

## Future Enhancements

- **Multi-AI Collaboration**: Multiple AIs working together on complex tasks
- **Dynamic Budget Allocation**: Automatically adjust budgets based on performance
- **Provider Performance Metrics**: Track success rates and quality by provider
- **Cost Prediction**: Estimate task costs before execution
- **Alert System**: Notify when budgets are exceeded or ROI drops
- **API Integration**: Direct integration with OpenAI, Anthropic, etc.

## Security & Privacy

- **No Credentials in Logs**: API keys never logged
- **Immutable Ledger**: Financial records are append-only
- **Audit Trail**: Complete transparency of all operations
- **Budget Enforcement**: Hard limits prevent runaway costs

## Related Documentation

- `docs/AUDIT_SYSTEM.md` - Audit logging system
- `audit/README.md` - Audit viewer usage
- `AI_POLICY.md` - AI agent policies
- `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` - Project roadmap
