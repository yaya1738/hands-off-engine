# API Reference

Complete reference for all Python modules and their public interfaces in the Hands-Off Engine.

## Table of Contents

1. [Core Pipeline Modules](#core-pipeline-modules)
   - [Alpha Module](#alpha-module)
   - [Decider Module](#decider-module)
   - [Executor Module](#executor-module)
2. [Supporting Modules](#supporting-modules)
   - [Audit Module](#audit-module)
   - [AI Nexus](#ai-nexus)
   - [AI Intake Handler](#ai-intake-handler)
3. [Scripts](#scripts)
   - [Pipeline Runner](#pipeline-runner)
4. [Error Handling](#error-handling)

---

## Core Pipeline Modules

### Alpha Module

#### `alpha.sync_polymarket_model`

**Purpose**: Transform live Polymarket data into canonical alpha signals for the Decider.

**Key Functions**:

##### `sync_polymarket_model(input_path, output_path, max_markets=20)`

Main sync function that transforms compact market data into the canonical model format.

**Parameters**:
- `input_path` (Path): Path to polymarket-compact.json input file
- `output_path` (Path): Path where polymarket-model.json will be written
- `max_markets` (int, optional): Maximum number of markets to include (default: 20)

**Returns**:
- `dict`: The generated model dictionary with keys:
  - `generated_at`: ISO timestamp
  - `source_timestamp`: Original data timestamp
  - `total_markets_analyzed`: Total markets processed
  - `markets_selected`: Number of markets included
  - `markets`: List of market signal objects

**Raises**:
- `FileNotFoundError`: If input file doesn't exist

**Example**:
```python
from pathlib import Path
from alpha.sync_polymarket_model import sync_polymarket_model

input_path = Path('termux-hands-off/out/polymarket-compact.json')
output_path = Path('state/polymarket-model.json')

model = sync_polymarket_model(input_path, output_path, max_markets=15)
print(f"Selected {model['markets_selected']} markets")
```

##### `calculate_edge(market_price, fair_price)`

Calculate the edge between market price and fair price.

**Parameters**:
- `market_price` (float): Current market price (0.0 to 1.0)
- `fair_price` (float): Estimated fair price (0.0 to 1.0)

**Returns**:
- `float`: Absolute difference representing edge (e.g., 0.08 for 8%)

##### `estimate_fair_price(market)`

Estimate fair price from market data using a simple heuristic.

**Parameters**:
- `market` (dict): Market dictionary with keys like `bestBid`, `last`, `slug`

**Returns**:
- `float`: Estimated fair price clamped to [0.01, 0.99]

**Note**: This is a placeholder implementation. Production systems should use sophisticated alpha models.

##### `calculate_confidence(edge, market)`

Calculate confidence in an edge estimate.

**Parameters**:
- `edge` (float): Calculated edge value
- `market` (dict): Market dictionary with liquidity indicators

**Returns**:
- `float`: Confidence score (0.0 to 1.0)

**Logic**:
- Base confidence: 0.7
- Reduces for high edges (>15%: 0.5x, >10%: 0.7x, >5%: 0.9x)
- Should adjust for liquidity in production

##### `determine_side(market_price, fair_price)`

Determine which side to bet on.

**Parameters**:
- `market_price` (float): Current market price
- `fair_price` (float): Estimated fair price

**Returns**:
- `str`: "YES" if fair_price > market_price, else "NO"

##### `transform_market(market, query)`

Transform a raw market into canonical model format.

**Parameters**:
- `market` (dict): Raw market data
- `query` (str): Query category for this market

**Returns**:
- `dict` or `None`: Transformed market dict (None if filtered out)

**Filters applied**:
- Excludes markets with extreme prices (< 0.05 or > 0.95)
- Excludes markets with edge < 5%

---

### Decider Module

#### `decider.ho_decider`

**Purpose**: The "Brain" that converts alpha signals into structured planned actions.

**Key Classes**:

##### `PlannedAction` (dataclass)

Structured representation of a planned trading action.

**Attributes**:
- `market_id` (str): Market identifier slug
- `market_name` (str): Human-readable market question
- `side` (str): Trade direction ("YES" or "NO")
- `amount` (float): Dollar amount to risk
- `confidence` (float): Confidence score (0.0 to 1.0)
- `reasoning` (str): Explanation for this action

**Example**:
```python
from decider.ho_decider import PlannedAction

action = PlannedAction(
    market_id="trump-macron-november",
    market_name="Will Trump talk to Macron in November?",
    side="NO",
    amount=45.0,
    confidence=0.78,
    reasoning="Edge: 8.5%, Current odds: 0.42, Confidence: 78%"
)
```

##### `Decider` class

The brain of the pipeline that produces planned actions from alpha signals.

**Constructor**:
```python
Decider(bankroll=1000.0)
```

**Parameters**:
- `bankroll` (float, optional): Total bankroll for position sizing (default: $1000)

**Methods**:

###### `load_model_signals(model_path)`

Load alpha signals from polymarket-model.json file.

**Parameters**:
- `model_path` (Path): Path to polymarket-model.json

**Returns**:
- `List[dict]`: List of alpha signal dictionaries

**Example**:
```python
from pathlib import Path
from decider.ho_decider import Decider

decider = Decider(bankroll=1000.0)
signals = decider.load_model_signals(Path('state/polymarket-model.json'))
```

###### `plan_actions(alpha_signals)`

Convert alpha signals into planned actions using Kelly criterion.

**Parameters**:
- `alpha_signals` (List[dict]): List of signal dicts with keys:
  - `market_id`: Market identifier
  - `market_name`: Market question
  - `edge`: Expected edge (e.g., 0.05 for 5%)
  - `current_odds`: Current market odds
  - `side`: "YES" or "NO"
  - `model_confidence`: Confidence score (optional)
  - `fair_price`: Estimated fair price (optional)

**Returns**:
- `List[PlannedAction]`: List of planned trading actions

**Position Sizing Logic**:
1. Calculate Kelly fraction: `edge × confidence`
2. Cap at 10% of bankroll (max_fraction)
3. Apply dollar amount: `bankroll × size_fraction`
4. Result clamped by executor's MAX_POSITION_SIZE

**Example**:
```python
decider = Decider(bankroll=1000.0)
signals = [
    {
        'market_id': 'example-market',
        'market_name': 'Example Market?',
        'edge': 0.08,
        'current_odds': 0.42,
        'side': 'NO',
        'model_confidence': 0.75
    }
]
actions = decider.plan_actions(signals)
for action in actions:
    print(f"{action.market_name}: ${action.amount:.2f} on {action.side}")
```

---

### Executor Module

#### `executor.ho_executor_plan`

**Purpose**: The "Body + Reflexes" that validates and executes planned actions with safety checks.

**Key Classes**:

##### `ExecutionResult` (dataclass)

Result of attempting to execute a planned action.

**Attributes**:
- `market_id` (str): Market identifier
- `market_name` (str): Market question
- `success` (bool): Whether execution succeeded
- `message` (str): Human-readable status message
- `executed_amount` (float, optional): Amount executed (default: 0.0)

**Example**:
```python
from executor.ho_executor_plan import ExecutionResult

result = ExecutionResult(
    market_id="example-market",
    market_name="Example?",
    success=True,
    message="DRYRUN: Would place NO order for $45.00",
    executed_amount=45.0
)
```

##### `Executor` class

The body and reflexes that validate and execute planned actions.

**Safety Parameters** (class attributes):
- `MAX_POSITION_SIZE` = 100.0 (Maximum dollars per position)
- `MIN_CONFIDENCE_THRESHOLD` = 0.7 (Minimum confidence to execute)

**Constructor**:
```python
Executor(dryrun=True)
```

**Parameters**:
- `dryrun` (bool, optional): If True, no actual trades executed (default: True)

**Methods**:

###### `validate_action(action)`

Validate a planned action against safety rules (reflexes).

**Parameters**:
- `action` (PlannedAction): Action to validate

**Returns**:
- `tuple[bool, str]`: (is_valid, error_message)
  - `is_valid`: True if action passes all checks
  - `error_message`: "OK" if valid, else description of failure

**Validation Rules**:
1. Confidence must be ≥ 70%
2. Amount must be ≤ $100
3. Side must be "YES" or "NO"

**Example**:
```python
from executor.ho_executor_plan import Executor
from decider.ho_decider import PlannedAction

executor = Executor(dryrun=True)
action = PlannedAction(
    market_id="test",
    market_name="Test?",
    side="YES",
    amount=50.0,
    confidence=0.75,
    reasoning="Test"
)

is_valid, msg = executor.validate_action(action)
if is_valid:
    print("Action passed validation")
else:
    print(f"Action rejected: {msg}")
```

###### `execute_actions(planned_actions)`

Execute a list of planned actions with safety validation.

**Parameters**:
- `planned_actions` (List[PlannedAction]): Actions to execute

**Returns**:
- `List[ExecutionResult]`: Execution results for each action

**Behavior**:
- Validates each action before execution
- Rejects invalid actions with detailed message
- In DRYRUN mode: logs what would be done
- In LIVE mode: executes actual trades (requires explicit approval)

**Example**:
```python
from executor.ho_executor_plan import Executor
from decider.ho_decider import Decider
from pathlib import Path

# Plan actions
decider = Decider(bankroll=1000.0)
signals = decider.load_model_signals(Path('state/polymarket-model.json'))
actions = decider.plan_actions(signals)

# Execute with validation
executor = Executor(dryrun=True)
results = executor.execute_actions(actions)

for result in results:
    status = "✓" if result.success else "✗"
    print(f"{status} {result.market_name}: {result.message}")
```

###### `get_execution_summary(results)`

Generate summary statistics for execution results.

**Parameters**:
- `results` (List[ExecutionResult]): Execution results to summarize

**Returns**:
- `dict`: Summary with keys:
  - `total_actions`: Total number of actions
  - `successful`: Number of successful executions
  - `rejected`: Number of rejected actions
  - `total_amount_executed`: Sum of executed amounts
  - `mode`: "DRYRUN" or "LIVE"

**Example**:
```python
executor = Executor(dryrun=True)
results = executor.execute_actions(actions)
summary = executor.get_execution_summary(results)

print(f"Executed {summary['successful']}/{summary['total_actions']} actions")
print(f"Total amount: ${summary['total_amount_executed']:.2f}")
print(f"Mode: {summary['mode']}")
```

---

## Supporting Modules

### Audit Module

#### `audit.audit_logger`

**Purpose**: Provide structured, immutable audit logging for all critical operations.

**Key Classes**:

##### `AuditLogger` class

Central audit logger for the Hands-Off Engine.

**Event Type Constants**:
- `EVENT_DECISION` = "decision"
- `EVENT_ACTION` = "action"
- `EVENT_DATA_FETCH` = "data_fetch"
- `EVENT_STATE_CHANGE` = "state_change"
- `EVENT_RISK_ASSESSMENT` = "risk_assessment"
- `EVENT_ALPHA_CALCULATION` = "alpha_calculation"
- `EVENT_EDGE_DETECTION` = "edge_detection"
- `EVENT_ORDER` = "order"
- `EVENT_EXECUTION` = "execution"
- `EVENT_ERROR` = "error"

**Constructor**:
```python
AuditLogger(log_dir=None, component="unknown")
```

**Parameters**:
- `log_dir` (str, optional): Directory for audit logs. Defaults to `~/hands-off/audit` or `./logs/audit`
- `component` (str, optional): Name of component using logger (default: "unknown")

**Log File Format**: JSONL (JSON Lines) with daily rotation: `audit_YYYY-MM-DD.jsonl`

**Methods**:

###### `log(event_type, event_data, severity="info", session_id=None)`

Log a generic audit event.

**Parameters**:
- `event_type` (str): Type of event (use EVENT_* constants)
- `event_data` (dict): Event-specific data
- `severity` (str, optional): Severity level (debug/info/warning/error/critical)
- `session_id` (str, optional): Session identifier for grouping related events

**Example**:
```python
from audit import get_audit_logger

audit = get_audit_logger(component="my_module")
audit.log(
    event_type=audit.EVENT_DECISION,
    event_data={"decision": "buy", "amount": 50.0},
    severity="info",
    session_id="session_123"
)
```

###### `log_decision(decision_type, inputs, outputs, metadata=None, session_id=None)`

Log a decision event (alpha, risk, sizing, etc.).

**Parameters**:
- `decision_type` (str): Type of decision
- `inputs` (dict): Input parameters to decision
- `outputs` (dict): Output/results of decision
- `metadata` (dict, optional): Additional context
- `session_id` (str, optional): Session identifier

**Example**:
```python
audit.log_decision(
    decision_type="position_sizing",
    inputs={"edge": 0.08, "bankroll": 1000.0},
    outputs={"size": 50.0, "kelly_fraction": 0.05},
    metadata={"market_id": "example-market"}
)
```

###### `log_action(action_type, action_data, result=None, session_id=None)`

Log an action event (trade, order, state change).

**Parameters**:
- `action_type` (str): Type of action
- `action_data` (dict): Action details
- `result` (str, optional): Action result/outcome
- `session_id` (str, optional): Session identifier

###### `log_data_fetch(source, params, success, record_count=None, error=None, session_id=None)`

Log a data fetch event.

**Parameters**:
- `source` (str): Data source identifier
- `params` (dict): Fetch parameters
- `success` (bool): Whether fetch succeeded
- `record_count` (int, optional): Number of records fetched
- `error` (str, optional): Error message if failed
- `session_id` (str, optional): Session identifier

###### `log_edge_detection(market, p_fair, p_market, edge, action, metadata=None, session_id=None)`

Log an edge detection event.

**Parameters**:
- `market` (str): Market identifier
- `p_fair` (float): Fair price estimate
- `p_market` (float): Current market price
- `edge` (float): Calculated edge
- `action` (str): Recommended action
- `metadata` (dict, optional): Additional context
- `session_id` (str, optional): Session identifier

###### `log_order(order_type, market, side, size, price=None, dryrun=True, order_id=None, session_id=None)`

Log an order event.

**Parameters**:
- `order_type` (str): Type of order (limit/market)
- `market` (str): Market identifier
- `side` (str): Order side (YES/NO)
- `size` (float): Order size in dollars
- `price` (float, optional): Limit price
- `dryrun` (bool, optional): DRYRUN mode flag (default: True)
- `order_id` (str, optional): Order identifier
- `session_id` (str, optional): Session identifier

###### `log_state_change(state_type, previous_state, new_state, reason=None, session_id=None)`

Log a state change event.

**Parameters**:
- `state_type` (str): Type of state being changed
- `previous_state` (any): Previous state value
- `new_state` (any): New state value
- `reason` (str, optional): Reason for change
- `session_id` (str, optional): Session identifier

##### `get_audit_logger(component, log_dir=None)`

Factory function to get or create an audit logger instance.

**Parameters**:
- `component` (str): Component name
- `log_dir` (str, optional): Log directory path

**Returns**:
- `AuditLogger`: Logger instance

**Example**:
```python
from audit import get_audit_logger

audit = get_audit_logger(component="alpha.polymarket")
audit.log_action(
    action_type="sync_model",
    action_data={"markets": 15},
    result="success"
)
```

---

### AI Nexus

#### `ai_nexus.nexus`

**Purpose**: Multi-brain orchestration system for coordinating multiple AI agents.

**Key Classes & Enums**:

##### `AIProvider` (Enum)

Supported AI providers:
- `COPILOT` = "copilot"
- `CHATGPT` = "chatgpt"
- `CLAUDE` = "claude"
- `OPENAI` = "openai"
- `ANTHROPIC` = "anthropic"

##### `TaskPriority` (Enum)

Task priority levels:
- `CRITICAL` = "critical"
- `HIGH` = "high"
- `MEDIUM` = "medium"
- `LOW` = "low"

##### `TaskStatus` (Enum)

Task execution status:
- `PENDING` = "pending"
- `IN_PROGRESS` = "in_progress"
- `COMPLETED` = "completed"
- `FAILED` = "failed"
- `CANCELLED` = "cancelled"

##### `AITask` (dataclass)

Represents a task to be executed by an AI agent.

**Attributes**:
- `task_id` (str): Unique task identifier
- `task_type` (str): Type of task (plan/code/analyze/decide)
- `description` (str): Task description
- `priority` (TaskPriority): Task priority
- `provider` (AIProvider, optional): AI provider (auto-select if None)
- `context` (dict, optional): Task context data
- `max_cost` (float, optional): Cost limit in USD
- `timeout` (int, optional): Timeout in seconds
- `created_at` (str): ISO timestamp (auto-generated)

**Methods**:
- `to_dict()`: Convert to dictionary for serialization

##### `AIResult` (dataclass)

Result from AI task execution.

**Attributes**:
- `task_id` (str): Task identifier
- `status` (TaskStatus): Execution status
- `provider` (AIProvider): AI provider used
- `output` (any): Task output/result
- `cost` (float): Cost in USD (default: 0.0)
- `tokens_used` (int): Tokens consumed (default: 0)
- `execution_time` (float): Time in seconds (default: 0.0)
- `error` (str, optional): Error message if failed
- `completed_at` (str): ISO timestamp (auto-generated)

**Methods**:
- `to_dict()`: Convert to dictionary for serialization

---

### AI Intake Handler

#### `ai.ai_intake_handler`

**Purpose**: Handle commands posted as issue comments on the designated AI Intake issue.

**Key Functions**:

##### `load_text(path)`

Load text from a file, return warning if not found.

**Parameters**:
- `path` (str): File path to read

**Returns**:
- `str`: File content or warning message

##### `post_comment(repo, issue_number, body)`

Post a comment back to GitHub issue via API.

**Parameters**:
- `repo` (str): Repository identifier (owner/repo)
- `issue_number` (int): Issue number
- `body` (str): Comment body text

**Raises**:
- `requests.HTTPError`: If API call fails

**Requires Environment Variables**:
- `GITHUB_TOKEN`: GitHub API token
- `GITHUB_API_URL`: GitHub API URL (optional, defaults to https://api.github.com)

##### `run_plan(event)`

Handle `/plan` command to generate a roadmap-aligned plan.

**Parameters**:
- `event` (dict): GitHub webhook event payload

**Process**:
1. Loads AI policy and research report
2. Analyzes issue description
3. Generates plan using OpenAI
4. Posts plan as comment on issue
5. Logs all actions to audit trail

**Requires Environment Variables**:
- `GITHUB_TOKEN`: GitHub API token
- `GITHUB_REPOSITORY`: Repository identifier
- `OPENAI_API_KEY`: OpenAI API key

---

## Scripts

### Pipeline Runner

#### `scripts.run_pipeline`

**Purpose**: Run the complete end-to-end pipeline.

**Key Functions**:

##### `run_pipeline(bankroll=1000.0, dryrun=True, verbose=True)`

Run the full pipeline from alpha to execution.

**Parameters**:
- `bankroll` (float, optional): Total bankroll for sizing (default: 1000.0)
- `dryrun` (bool, optional): DRYRUN mode flag (default: True)
- `verbose` (bool, optional): Print detailed progress (default: True)

**Returns**:
- `dict`: Pipeline results with keys:
  - `start_time`: ISO timestamp
  - `success`: Overall success flag
  - `error`: Error message if failed
  - `steps`: Dict of step results

**Pipeline Steps**:
1. **Sync Alpha Signals**: Load and transform market data
2. **Plan Actions**: Decider converts signals to actions
3. **Execute Actions**: Executor validates and executes with safety checks

**Example**:
```python
from scripts.run_pipeline import run_pipeline

results = run_pipeline(
    bankroll=1000.0,
    dryrun=True,
    verbose=True
)

if results['success']:
    print("Pipeline completed successfully!")
    print(f"Actions planned: {results['steps']['decide']['actions_count']}")
    print(f"Actions executed: {results['steps']['execute']['successful']}")
else:
    print(f"Pipeline failed: {results['error']}")
```

**CLI Usage**:
```bash
python3 scripts/run_pipeline.py
```

---

## Error Handling

### Common Exceptions

All modules follow graceful degradation patterns:

1. **FileNotFoundError**: Raised when required input files don't exist
   - **Recovery**: Ensure input files are in expected locations
   - **Example**: Missing `polymarket-compact.json`

2. **ValidationError**: Raised when data doesn't meet schema requirements
   - **Recovery**: Check data format matches expected schemas
   - **Example**: Invalid market data structure

3. **AuditError**: Logged to stderr if audit file writes fail
   - **Recovery**: System continues but logs to stderr
   - **Example**: Disk full or permission issues

### Error Handling Patterns

#### Atomic File Writes

All state files use atomic writes to prevent corruption:

```python
# Write to temp file first
output_tmp = output_path.with_suffix('.tmp')
with open(output_tmp, 'w') as f:
    json.dump(data, f, indent=2)

# Atomic move (on Unix systems)
output_tmp.replace(output_path)
```

#### Graceful Degradation

Audit logging never crashes the application:

```python
try:
    audit.log_action(...)
except Exception as e:
    # Fallback to stderr
    print(f"[AUDIT ERROR] {e}", file=sys.stderr)
```

#### Optional Dependencies

History logging is optional and doesn't break core functionality:

```python
try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    log_kernel_history_event = None

# Later in code:
if log_kernel_history_event:
    log_kernel_history_event(...)
```

---

## Usage Examples

### Complete Pipeline Example

```python
#!/usr/bin/env python3
"""Example: Run complete trading pipeline"""

from pathlib import Path
from scripts.run_pipeline import run_pipeline

def main():
    # Run pipeline in DRYRUN mode with $1000 bankroll
    results = run_pipeline(
        bankroll=1000.0,
        dryrun=True,
        verbose=True
    )
    
    if results['success']:
        print("\n✓ Pipeline completed successfully")
        
        # Show results
        sync = results['steps']['sync']
        decide = results['steps']['decide']
        execute = results['steps']['execute']
        
        print(f"\nAlpha: {sync['markets_selected']} markets selected")
        print(f"Decider: {decide['actions_count']} actions planned")
        print(f"Executor: {execute['successful']}/{execute['total_actions']} executed")
        print(f"Total risk: ${execute['total_amount_executed']:.2f}")
        
        return 0
    else:
        print(f"\n✗ Pipeline failed: {results['error']}")
        return 1

if __name__ == '__main__':
    exit(main())
```

### Custom Alpha + Decider Example

```python
#!/usr/bin/env python3
"""Example: Custom alpha signals with Decider"""

from decider.ho_decider import Decider, PlannedAction
from executor.ho_executor_plan import Executor

# Custom alpha signals (e.g., from your own model)
custom_signals = [
    {
        'market_id': 'btc-100k-2024',
        'market_name': 'Will Bitcoin reach $100k in 2024?',
        'edge': 0.12,
        'current_odds': 0.35,
        'side': 'YES',
        'model_confidence': 0.68,
        'fair_price': 0.47
    },
    {
        'market_id': 'eth-5k-2024',
        'market_name': 'Will Ethereum reach $5k in 2024?',
        'edge': 0.08,
        'current_odds': 0.52,
        'side': 'NO',
        'model_confidence': 0.71,
        'fair_price': 0.44
    }
]

# Plan actions
decider = Decider(bankroll=1000.0)
actions = decider.plan_actions(custom_signals)

print(f"Planned {len(actions)} actions:\n")
for action in actions:
    print(f"  ${action.amount:.2f} on {action.side} - {action.market_name}")
    print(f"    Confidence: {action.confidence:.1%}")
    print(f"    Reasoning: {action.reasoning}\n")

# Execute with safety checks
executor = Executor(dryrun=True)
results = executor.execute_actions(actions)

# Show results
summary = executor.get_execution_summary(results)
print(f"\nExecution Summary:")
print(f"  Mode: {summary['mode']}")
print(f"  Successful: {summary['successful']}/{summary['total_actions']}")
print(f"  Rejected: {summary['rejected']}")
print(f"  Total amount: ${summary['total_amount_executed']:.2f}")
```

### Audit Logging Example

```python
#!/usr/bin/env python3
"""Example: Comprehensive audit logging"""

from audit import get_audit_logger
import time

# Get logger for component
audit = get_audit_logger(component="example_trader")

# Start session
session_id = f"session_{int(time.time())}"

# Log data fetch
audit.log_data_fetch(
    source="polymarket_api",
    params={"query": "bitcoin", "limit": 10},
    success=True,
    record_count=10,
    session_id=session_id
)

# Log edge detection
audit.log_edge_detection(
    market="btc-100k-2024",
    p_fair=0.47,
    p_market=0.35,
    edge=0.12,
    action="BUY_YES",
    metadata={"confidence": 0.68},
    session_id=session_id
)

# Log decision
audit.log_decision(
    decision_type="position_sizing",
    inputs={"edge": 0.12, "confidence": 0.68, "bankroll": 1000.0},
    outputs={"kelly_fraction": 0.0816, "size": 81.6},
    session_id=session_id
)

# Log order (DRYRUN)
audit.log_order(
    order_type="limit",
    market="btc-100k-2024",
    side="YES",
    size=81.6,
    price=0.35,
    dryrun=True,
    session_id=session_id
)

print(f"Audit events logged to session: {session_id}")
print("Check logs/audit/audit_YYYY-MM-DD.jsonl")
```

---

## Type Hints Reference

All public functions use Python type hints:

```python
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

# Example function signatures
def sync_polymarket_model(
    input_path: Path,
    output_path: Path,
    max_markets: int = 20
) -> Dict: ...

def plan_actions(
    alpha_signals: List[dict]
) -> List[PlannedAction]: ...

def validate_action(
    action: PlannedAction
) -> tuple[bool, str]: ...

def log_decision(
    decision_type: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> None: ...
```

---

## Module Dependencies

```
scripts/run_pipeline.py
├── alpha/sync_polymarket_model.py
├── decider/ho_decider.py
│   └── audit/audit_logger.py
└── executor/ho_executor_plan.py
    └── audit/audit_logger.py

ai/ai_intake_handler.py
└── audit/audit_logger.py

ai_nexus/nexus.py
└── audit/audit_logger.py
```

**Key Pattern**: All core modules depend on `audit` for logging, but audit has no dependencies.

---

## Version Information

- **Python Version**: 3.12+
- **Type Hints**: Full support (PEP 484, 526)
- **Dataclasses**: Used for structured data (PEP 557)
- **Path Objects**: `pathlib.Path` preferred over strings

---

## Next Steps

- See [DATA_SCHEMAS.md](DATA_SCHEMAS.md) for JSON file formats
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for setup instructions
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
