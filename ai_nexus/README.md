# AI Nexus - Multi-Brain Orchestration System

**Comprehensive audit logging, financial tracking, and self-improving AI operations for the Hands-Off Engine**

## Overview

AI Nexus is a multi-brain orchestration system that coordinates multiple AI providers (Claude, ChatGPT, Copilot) with comprehensive tracking, self-improvement, and self-financing capabilities.

### Key Features

✅ **Multi-AI Orchestration**
- Unified interface for Claude, OpenAI GPT models, and GitHub Copilot
- Route requests to appropriate providers based on task requirements
- Track all AI actions through centralized audit system

✅ **Comprehensive Audit Logging**
- Immutable, append-only event logs
- Session-based tracking
- Component-level filtering
- Full traceability of all AI operations

✅ **Financial Ledger**
- Blockchain-inspired hash-chained ledger
- Tracks all costs and revenues
- Cryptographic verification of integrity
- Real-time ROI calculation

✅ **Self-Improvement**
- Analyzes performance metrics automatically
- Generates actionable recommendations
- Identifies cost optimization opportunities
- Detects reliability issues

✅ **Self-Financing**
- Monitors profitability in real-time
- Automatically adjusts budgets based on ROI
- Scales profitable operations
- Reduces or pauses unprofitable activities
- Reinvests profits into high-ROI components

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Nexus Core                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            Multi-Brain Orchestration                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │  Claude  │  │  OpenAI  │  │ Copilot  │         │  │
│  │  └──────────┘  └──────────┘  └──────────┘         │  │
│  └─────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Audit & Financial Layer                │  │
│  │  ┌──────────────────┐  ┌──────────────────┐       │  │
│  │  │  Audit Logger    │  │  Financial Ledger│       │  │
│  │  │  - Event Logs    │  │  - Costs         │       │  │
│  │  │  - Session Track │  │  - Revenues      │       │  │
│  │  │  - Component     │  │  - ROI           │       │  │
│  │  └──────────────────┘  └──────────────────┘       │  │
│  └─────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Intelligence & Optimization               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐       │  │
│  │  │ Self-Improvement │  │  Self-Financing  │       │  │
│  │  │  - Performance   │  │  - Budget Adjust │       │  │
│  │  │  - Recommendations│  │  - Scaling      │       │  │
│  │  │  - Error Analysis│  │  - Sustainability│       │  │
│  │  └──────────────────┘  └──────────────────┘       │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# No additional dependencies needed - uses existing packages
# Ensure you have:
pip install openai requests
```

## Quick Start

### 1. Basic Usage

```python
from ai_nexus import NexusCore, OpenAIProvider, ClaudeProvider, AIRequest, AIProviderType
from audit import AuditLogger, FinancialLedger

# Initialize
audit_logger = AuditLogger()
ledger = FinancialLedger()
nexus = NexusCore(audit_logger=audit_logger, ledger=ledger)

# Register providers
nexus.register_provider(OpenAIProvider(audit_logger, ledger))
nexus.register_provider(ClaudeProvider(audit_logger, ledger))

# Make a request
request = AIRequest(
    provider_type=AIProviderType.OPENAI,
    action="code_generation",
    prompt="Write a function to calculate fibonacci numbers",
    model="gpt-4o-mini"
)

response = nexus.execute_request(request)
print(f"Cost: ${response.cost:.4f}")
print(f"Response: {response.content}")
```

### 2. Track Revenue

```python
# Record revenue from AI-driven trading
nexus.record_revenue(
    component="trading.polymarket",
    action="trade_execution",
    amount=50.00,  # $50 profit
    metadata={"market": "election_2024", "position": "YES"}
)
```

### 3. Get Metrics

```python
# Get comprehensive session metrics
metrics = nexus.get_session_metrics()
print(f"Total Cost: ${metrics['financial']['total_costs']:.2f}")
print(f"Total Revenue: ${metrics['financial']['total_revenue']:.2f}")
print(f"ROI: {metrics['financial']['roi_percent']:.1f}%")
```

## Command-Line Tools

### Audit Log Viewer

View and analyze audit logs:

```bash
# View recent events
python3 audit/audit_viewer.py

# Filter by component
python3 audit/audit_viewer.py --component ai.claude

# Show session summary
python3 audit/audit_viewer.py --session <session-id> --summary

# Show verbose metadata
python3 audit/audit_viewer.py --metadata --limit 10
```

### Real-Time Monitor

Monitor AI Nexus in real-time:

```bash
# Start monitoring dashboard (refreshes every 5 seconds)
python3 ai_nexus/nexus_monitor.py

# Monitor specific session
python3 ai_nexus/nexus_monitor.py --session <session-id>

# Run once without continuous monitoring
python3 ai_nexus/nexus_monitor.py --once

# Custom refresh interval
python3 ai_nexus/nexus_monitor.py --refresh 10
```

The monitor displays:
- System status and event counts
- Financial performance (costs, revenue, profit, ROI)
- Component performance breakdown
- Self-improvement recommendations
- Self-financing status
- Ledger integrity verification

## Self-Improvement

The self-improvement engine analyzes performance and generates recommendations:

```python
from ai_nexus.self_improvement import SelfImprovementEngine

engine = SelfImprovementEngine(audit_logger, ledger)

# Get recommendations
recommendations = engine.generate_recommendations()
for rec in recommendations:
    print(f"[{rec.priority}] {rec.title}")
    print(f"  {rec.description}")
    print(f"  Expected Impact: {rec.expected_impact}")

# Get optimal budget allocation
allocations = engine.get_optimal_budget_allocation()
for component, allocation in allocations.items():
    print(f"{component}:")
    print(f"  Current: ${allocation['current_budget']:.2f}")
    print(f"  Recommended: ${allocation['recommended_budget']:.2f}")
    print(f"  ROI: {allocation['current_roi']:.1f}%")
```

## Self-Financing

The self-financing engine automatically manages budgets:

```python
from ai_nexus.self_financing import SelfFinancingEngine

engine = SelfFinancingEngine(audit_logger, ledger)

# Get financing decisions
decisions = engine.analyze_and_decide()
for decision in decisions:
    print(f"{decision.component}: {decision.action}")
    print(f"  Current Budget: ${decision.current_budget:.2f}")
    print(f"  Recommended: ${decision.recommended_budget:.2f}")
    print(f"  Reasoning: {decision.reasoning}")

# Calculate profit reinvestment
reinvestment = engine.calculate_profit_reinvestment()
for component, amount in reinvestment.items():
    print(f"Allocate ${amount:.2f} to {component}")

# Get sustainability report
report = engine.get_sustainability_report()
print(f"Status: {report['sustainability_status']}")
print(f"Net Profit: ${report['net_profit']:.2f}")
print(f"ROI: {report['roi_percent']:.1f}%")
```

## Integration with Existing Systems

### AI Intake Handler

The AI intake handler is now fully integrated with AI Nexus:

- All `/plan` commands are tracked
- Costs are automatically logged
- Session metrics are displayed
- Full audit trail is maintained

### Claude Integration

Track Claude Code actions:

```python
from ai_nexus import ClaudeProvider

claude = ClaudeProvider(audit_logger, ledger)

# Log a code generation action
claude.log_action(
    action="code_generation",
    files_changed=5,
    lines_added=150,
    lines_removed=20,
    metadata={"task": "implement_feature_x"}
)
```

### Copilot Integration

Track GitHub Copilot actions:

```python
from ai_nexus import CopilotProvider

copilot = CopilotProvider(audit_logger, ledger)

# Log code completions
copilot.log_action(
    action="code_completion",
    suggestions_accepted=15,
    lines_added=45,
    metadata={"language": "python"}
)
```

## Financial Tracking

### Adding Costs

```python
ledger.add_cost(
    component="ai.openai",
    action="plan_generation",
    amount=0.0234,  # $0.0234
    session_id=session_id,
    metadata={"model": "gpt-4o-mini", "tokens": 1500}
)
```

### Adding Revenue

```python
ledger.add_revenue(
    component="trading.polymarket",
    action="trade_profit",
    amount=50.00,  # $50 profit
    session_id=session_id,
    metadata={"market": "election_2024"}
)
```

### Querying Balance

```python
balance = ledger.get_balance()
print(f"Total Costs: ${balance['total_costs']:.2f}")
print(f"Total Revenue: ${balance['total_revenue']:.2f}")
print(f"Net Profit: ${balance['net_profit']:.2f}")
print(f"ROI: {balance['roi_percent']:.1f}%")
```

### Verify Integrity

```python
is_valid = ledger.verify_integrity()
print(f"Ledger Integrity: {'✅ VALID' if is_valid else '❌ COMPROMISED'}")
```

## ROI Thresholds

The self-financing system uses these thresholds:

- **Scale Up** (ROI > 100%): Double the budget
- **Maintain** (ROI > 20%): Slight increase (20%)
- **Scale Down** (0% < ROI < 20%): Maintain or reduce
- **Pause** (ROI < -50%): Stop operations

## Cost Estimation

### OpenAI Pricing

| Model | Input ($/MTok) | Output ($/MTok) |
|-------|----------------|-----------------|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o-mini | $0.15 | $0.60 |
| GPT-4-turbo | $10.00 | $30.00 |

### Claude Pricing

| Model | Input ($/MTok) | Output ($/MTok) |
|-------|----------------|-----------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

### Copilot

- Flat rate: $10/month
- Amortized: ~$0.01 per action

## File Structure

```
ai_nexus/
├── __init__.py                 # Package exports
├── nexus_core.py               # Core orchestration system
├── provider_claude.py          # Claude provider
├── provider_openai.py          # OpenAI provider
├── provider_copilot.py         # Copilot provider
├── self_improvement.py         # Self-improvement engine
├── self_financing.py           # Self-financing engine
├── nexus_monitor.py            # Real-time monitoring dashboard
└── README.md                   # This file

audit/
├── __init__.py                 # Package exports
├── audit_logger.py             # Audit logging system
├── ledger.py                   # Financial ledger
├── audit_viewer.py             # CLI tool for viewing logs
└── logs/                       # Log files (auto-created)
    ├── ai_claude.jsonl         # Claude events
    ├── ai_openai.jsonl         # OpenAI events
    ├── ai_copilot.jsonl        # Copilot events
    ├── trading_polymarket.jsonl # Trading events
    └── session_*.jsonl         # Session-specific logs

ledger.jsonl                    # Financial ledger (immutable)
```

## Example Session

```python
from ai_nexus import *
from audit import *

# Initialize system
audit_logger = AuditLogger()
ledger = FinancialLedger()
nexus = NexusCore(audit_logger=audit_logger, ledger=ledger)

# Register providers
nexus.register_provider(OpenAIProvider(audit_logger, ledger))
nexus.register_provider(ClaudeProvider(audit_logger, ledger))

# AI Request 1: Generate trading plan
request = AIRequest(
    provider_type=AIProviderType.OPENAI,
    action="trading_analysis",
    prompt="Analyze market conditions for election trading",
    model="gpt-4o-mini"
)
response = nexus.execute_request(request)
# Cost: $0.0234

# AI Request 2: Generate code
request = AIRequest(
    provider_type=AIProviderType.OPENAI,
    action="code_generation",
    prompt="Write trading bot code",
    model="gpt-4o-mini"
)
response = nexus.execute_request(request)
# Cost: $0.0456

# Record trading revenue
nexus.record_revenue(
    component="trading.polymarket",
    action="trade_profit",
    amount=75.00  # $75 profit
)

# Get session metrics
metrics = nexus.get_session_metrics()
# Total Cost: $0.0690
# Total Revenue: $75.00
# Net Profit: $74.93
# ROI: 108,586%!

# Get self-improvement recommendations
from ai_nexus.self_improvement import SelfImprovementEngine
improvement = SelfImprovementEngine(audit_logger, ledger)
recommendations = improvement.generate_recommendations()
# ✅ Excellent ROI - Scale Up Recommended!

# Get self-financing decisions
from ai_nexus.self_financing import SelfFinancingEngine
financing = SelfFinancingEngine(audit_logger, ledger)
decisions = financing.analyze_and_decide()
# Recommendation: Double AI budget (ROI > 100%)
```

## Security

- **Immutable Logs**: Audit logs are append-only
- **Hash-Chained Ledger**: Financial ledger uses cryptographic hashing
- **Integrity Verification**: Detect any tampering with `verify_integrity()`
- **Session Isolation**: Each session has unique ID
- **No Data Deletion**: All events are permanently recorded

## Performance

- **Fast Logging**: Append-only writes are extremely fast
- **Efficient Queries**: Component and session indexes
- **Low Overhead**: Minimal impact on AI operations
- **Scalable**: Handles millions of events

## Future Enhancements

- [ ] Web dashboard for monitoring
- [ ] Real-time alerts for anomalies
- [ ] Machine learning-based optimization
- [ ] Multi-user support with RBAC
- [ ] Integration with more AI providers
- [ ] Automated A/B testing of models
- [ ] Cost prediction and budgeting
- [ ] Revenue forecasting

## Contributing

This system is part of the Hands-Off Engine. Contributions welcome!

## License

Part of the Hands-Off Engine project.
