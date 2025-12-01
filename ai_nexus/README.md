# AI Nexus - Multi-Brain Orchestration System

The AI Nexus is the central orchestration layer that coordinates multiple AI agents (Copilot, ChatGPT, Claude, etc.) with full audit trail, cost tracking, and financial ledger for self-financing capabilities.

It also provides a flexible, provider-based architecture for integrating multiple AI services with support for context files, retry logic, and structured result formats.

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

### Multi-AI Orchestration
- **Intelligent Routing**: Automatically selects the best AI provider based on task type, cost, and availability
- **Budget Management**: Enforces daily spending limits per provider
- **Cost Tracking**: Real-time monitoring of AI operation costs

### Provider-Based Architecture
- **Multi-Provider Support**: Easy integration of multiple AI providers (ChatGPT, Claude, Groq, Google)
- **Context-Aware Tasks**: Include context files to provide relevant information to AI models
- **Robust Error Handling**: Automatic retries with exponential backoff for transient failures

### Financial Ledger
- **Immutable Record**: All costs and revenues tracked in append-only ledger
- **ROI Calculation**: Track return on AI investment
- **Self-Financing**: Monitor whether AI operations are profitable

## Directory Structure

```
ai_nexus/
├── __init__.py              # Package initialization
├── nexus.py                 # Core orchestration
├── ledger.py                # Financial ledger
├── provider_chatgpt.py      # ChatGPT provider
├── provider_groq.py         # Groq provider (free tier)
├── provider_google.py       # Google AI provider (free tier)
├── multi_provider.py        # Auto-fallback between providers
├── runner.py                # Task dispatcher and executor
├── tasks/                   # Task definitions (JSON files)
└── output/                  # Task results (auto-generated)
```

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

### Using Providers Directly

```python
from ai_nexus import ChatGPTProvider

# Initialize provider
provider = ChatGPTProvider(
    model_name="gpt-4-1106-preview",
    max_retries=3,
    backoff_factor=1.5
)

# Define task
task = {
    "provider": "chatgpt",
    "prompt": "Analyze this code for potential bugs.",
    "context_files": [
        "executor/ho_executor_plan.py"
    ]
}

# Execute task
result = provider.run_task(task)
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

## Budget Limits

Default daily limits (configurable):
- **Copilot**: $100/day
- **ChatGPT**: $50/day
- **Claude**: $50/day
- **Groq**: Free tier
- **Google**: Free tier

## Storage

### Audit Logs
- Location: `logs/audit/audit_YYYY-MM-DD.jsonl`
- Format: JSON Lines (one event per line)

### Action Ledger
- Location: `logs/ledger/ledger_YYYY-MM-DD.jsonl`
- Format: JSON Lines (one entry per line)

## Security

- **No Credentials in Logs**: API keys never logged
- **Immutable Ledger**: Financial records are append-only
- **Audit Trail**: Complete transparency of all operations
- **Budget Enforcement**: Hard limits prevent runaway costs

## Related Documentation

- `docs/AUDIT_SYSTEM.md` - Audit logging system
- `AI_POLICY.md` - AI agent policies
