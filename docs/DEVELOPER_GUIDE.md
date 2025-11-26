# Developer Guide

Complete guide for developers working on the Hands-Off Engine, including setup, workflows, and coding standards.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Adding New Features](#adding-new-features)
7. [Debugging](#debugging)
8. [Contributing](#contributing)

---

## Quick Start

### Prerequisites

- **Python**: 3.12+ required
- **Git**: For version control
- **Text Editor**: VSCode, Vim, or any editor with Python support

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/yaya1738/hands-off-engine.git
cd hands-off-engine

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies (minimal - no heavy packages)
pip install requests openai

# 4. Run a test pipeline
python3 scripts/run_pipeline.py
```

**Note**: The test will fail if `polymarket-compact.json` doesn't exist. That's expected for initial setup.

---

## Development Setup

### Directory Structure

```
hands-off-engine/
├── alpha/              # Alpha signal generation
│   ├── ho_alpha_polymarket.py
│   └── sync_polymarket_model.py
├── decider/            # Decision logic (Brain)
│   └── ho_decider.py
├── executor/           # Execution logic (Body + Reflexes)
│   └── ho_executor_plan.py
├── audit/              # Audit logging infrastructure
│   ├── __init__.py
│   ├── audit_logger.py
│   └── audit_viewer.py
├── ai/                 # AI coordination
│   ├── ai_intake_handler.py
│   ├── approval_queue.py
│   └── autonomous_change.py
├── ai_nexus/           # Multi-agent orchestration
│   ├── nexus.py
│   ├── ledger.py
│   └── history_log.py
├── scripts/            # Utility scripts
│   ├── run_pipeline.py
│   ├── weekly_summary.py
│   └── ...
├── state/              # JSON state files
│   ├── polymarket-model.json
│   ├── knowledge.json
│   └── ...
├── logs/               # Log files
│   └── audit/          # Audit logs (JSONL)
├── docs/               # Documentation
│   ├── API_REFERENCE.md
│   ├── DATA_SCHEMAS.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPER_GUIDE.md
│   └── TROUBLESHOOTING.md
├── tests/              # Test suite
│   ├── test_alpha_pipeline.py
│   └── unit/
└── README.md
```

### Environment Setup

#### Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install minimal dependencies
pip install requests openai
```

#### Environment Variables (Optional)

Create `.env` file for local development:

```bash
# GitHub API (for AI intake handler)
GITHUB_TOKEN=your_github_token
GITHUB_REPOSITORY=yaya1738/hands-off-engine

# OpenAI API (for AI intake)
OPENAI_API_KEY=your_openai_key

# Polymarket API (future)
POLYMARKET_API_KEY=your_polymarket_key
```

**Note**: `.env` is in `.gitignore` - never commit secrets!

#### IDE Setup

**VSCode** (recommended):

```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.rulers": [88, 120]
  }
}
```

**Type Checking**:
```bash
pip install mypy
mypy alpha/sync_polymarket_model.py
```

---

## Development Workflow

### Before Making Changes

1. **Read Required Documents**:
   ```bash
   cat AI_POLICY.md
   cat termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md
   cat docs/RISK_MODEL_V1.md
   ```

2. **Check Current State**:
   ```bash
   git status
   git pull origin main
   ```

3. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Making Changes

#### 1. Write Code

Follow [Coding Standards](#coding-standards) section.

**Example** - Adding a new function:

```python
def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio for a series of returns.
    
    Args:
        returns: List of period returns (e.g., daily returns)
        risk_free_rate: Risk-free rate (default: 0.0)
    
    Returns:
        Sharpe ratio as float
    
    Raises:
        ValueError: If returns list is empty
    
    Example:
        >>> returns = [0.01, 0.02, -0.01, 0.03]
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe: {sharpe:.2f}")
    """
    if not returns:
        raise ValueError("Returns list cannot be empty")
    
    import numpy as np
    excess_returns = [r - risk_free_rate for r in returns]
    
    mean = np.mean(excess_returns)
    std = np.std(excess_returns)
    
    if std == 0:
        return 0.0
    
    return mean / std
```

#### 2. Add Tests

Create test file in `tests/`:

```python
# tests/test_metrics.py
import unittest
from your_module import calculate_sharpe_ratio

class TestSharpeRatio(unittest.TestCase):
    def test_positive_returns(self):
        returns = [0.01, 0.02, 0.03]
        sharpe = calculate_sharpe_ratio(returns)
        self.assertGreater(sharpe, 0)
    
    def test_empty_returns(self):
        with self.assertRaises(ValueError):
            calculate_sharpe_ratio([])
    
    def test_zero_volatility(self):
        returns = [0.02, 0.02, 0.02]
        sharpe = calculate_sharpe_ratio(returns)
        # Should handle division by zero gracefully
        self.assertTrue(isinstance(sharpe, float))

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python3 -m pytest tests/test_metrics.py -v
# or
python3 tests/test_metrics.py
```

#### 3. Update Documentation

Update relevant documentation:

```bash
# If adding new API
vim docs/API_REFERENCE.md

# If changing data schemas
vim docs/DATA_SCHEMAS.md

# If changing architecture
vim docs/ARCHITECTURE.md
```

#### 4. Audit Logging

Add audit logging for important operations:

```python
from audit import get_audit_logger

audit = get_audit_logger(component="metrics")

def calculate_metrics(data):
    session_id = f"metrics_{int(time.time())}"
    
    audit.log_action(
        action_type="calculate_metrics",
        action_data={"data_points": len(data)},
        session_id=session_id
    )
    
    # ... calculation logic ...
    
    audit.log_decision(
        decision_type="metric_calculation",
        inputs={"data_points": len(data)},
        outputs={"sharpe": sharpe, "sortino": sortino},
        session_id=session_id
    )
```

### Testing Changes

```bash
# Run unit tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_alpha_pipeline.py -v

# Run integration test (full pipeline)
python3 scripts/run_pipeline.py

# Check audit logs
tail -f logs/audit/audit_$(date +%Y-%m-%d).jsonl
```

### Committing Changes

```bash
# Stage changes
git add alpha/sync_polymarket_model.py
git add tests/test_alpha_pipeline.py
git add docs/API_REFERENCE.md

# Commit with descriptive message
git commit -m "Add Sharpe ratio calculation to metrics module

- Implement calculate_sharpe_ratio() with proper type hints
- Add comprehensive unit tests
- Update API reference documentation
- Add audit logging for metric calculations"

# Push to feature branch
git push origin feature/your-feature-name
```

### Creating Pull Request

1. Go to GitHub repository
2. Click "Pull Request"
3. Fill in:
   - **Title**: Clear, concise description
   - **Description**: What, why, how
   - **Checklist**: Use template below

**PR Template**:
```markdown
## Summary
Brief description of changes.

## Changes Made
- [ ] Added calculate_sharpe_ratio() function
- [ ] Updated API documentation
- [ ] Added unit tests
- [ ] Added audit logging

## Testing
- [x] Unit tests pass
- [x] Integration test passes
- [x] Audit logs verified

## Documentation
- [x] API reference updated
- [x] Added docstrings
- [x] Updated CHANGELOG (if applicable)

## Checklist
- [x] Code follows project style guide
- [x] All tests pass
- [x] Documentation updated
- [x] No secrets in code
- [x] Audit logging added (if applicable)
```

---

## Coding Standards

### Python Style

Follow **PEP 8** with these specifics:

#### Formatting

```python
# Line length: 88 characters (Black default)
# 120 characters max for complex lines

# Imports: stdlib, third-party, local
import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from openai import OpenAI

from audit import get_audit_logger
```

#### Naming Conventions

```python
# Functions: lowercase_with_underscores
def calculate_edge(market_price, fair_price):
    pass

# Classes: CapitalizedWords
class PlannedAction:
    pass

# Constants: UPPERCASE_WITH_UNDERSCORES
MAX_POSITION_SIZE = 100.0
MIN_CONFIDENCE_THRESHOLD = 0.7

# Private: _leading_underscore
def _internal_helper():
    pass
```

#### Type Hints

**Always use type hints** for public functions:

```python
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

def process_markets(
    markets: List[Dict[str, Any]],
    threshold: float = 0.05,
    output_path: Optional[Path] = None
) -> Tuple[List[Dict], int]:
    """
    Process markets and filter by threshold.
    
    Args:
        markets: List of market dictionaries
        threshold: Minimum edge threshold (default: 0.05)
        output_path: Optional path to write output
    
    Returns:
        Tuple of (filtered_markets, count)
    """
    filtered = [m for m in markets if m['edge'] >= threshold]
    return filtered, len(filtered)
```

#### Docstrings

Use **Google Style** docstrings:

```python
def complex_function(arg1: str, arg2: int, arg3: Optional[float] = None) -> Dict:
    """
    Short one-line summary.
    
    More detailed explanation if needed. Can span multiple
    lines and include background information.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        arg3: Optional arg3 description (default: None)
    
    Returns:
        Dictionary with keys:
            - key1: Description of key1
            - key2: Description of key2
    
    Raises:
        ValueError: If arg2 is negative
        FileNotFoundError: If input file missing
    
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        'value'
    
    Note:
        This function has important side effects or
        limitations worth noting.
    """
    if arg2 < 0:
        raise ValueError("arg2 must be non-negative")
    
    # Implementation...
    return {"key1": "value", "key2": arg2}
```

### Dataclasses for Structured Data

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlannedAction:
    """Structured representation of a planned trading action"""
    market_id: str
    market_name: str
    side: str  # "YES" or "NO"
    amount: float  # Dollar amount
    confidence: float  # 0.0 to 1.0
    reasoning: str
    
    def __post_init__(self):
        """Validate after initialization"""
        if self.side not in ["YES", "NO"]:
            raise ValueError(f"Invalid side: {self.side}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}")
```

### Error Handling

#### Graceful Degradation

```python
# Good: Graceful fallback
try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    log_kernel_history_event = None

# Later in code
if log_kernel_history_event:
    log_kernel_history_event(...)
```

#### Specific Exceptions

```python
# Good: Specific exceptions
def load_model(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
    
    return data

# Bad: Bare except
def load_model(path):
    try:
        # ... code ...
    except:  # Don't do this!
        pass
```

### File Operations

#### Atomic Writes

```python
from pathlib import Path
import json

def save_state(data: Dict, output_path: Path) -> None:
    """Save state with atomic write to prevent corruption"""
    # Write to temp file first
    output_tmp = output_path.with_suffix('.tmp')
    
    with open(output_tmp, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Atomic move (on Unix systems)
    output_tmp.replace(output_path)
```

#### Path Usage

```python
from pathlib import Path

# Good: Use Path objects
repo_root = Path(__file__).parent.parent
input_file = repo_root / 'state' / 'polymarket-model.json'

if input_file.exists():
    with open(input_file, 'r') as f:
        data = json.load(f)

# Bad: String concatenation
input_file = os.path.join(repo_root, 'state', 'polymarket-model.json')  # Less readable
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── test_alpha_pipeline.py      # Integration tests
└── unit/
    ├── test_sync_polymarket.py # Alpha module tests
    ├── test_decider.py         # Decider tests
    ├── test_executor.py        # Executor tests
    └── test_audit_logger.py    # Audit tests
```

### Writing Tests

#### Unit Tests

```python
import unittest
from decider.ho_decider import Decider, PlannedAction

class TestDecider(unittest.TestCase):
    def setUp(self):
        """Run before each test"""
        self.decider = Decider(bankroll=1000.0)
    
    def test_plan_actions_basic(self):
        """Test basic action planning"""
        signals = [{
            'market_id': 'test-market',
            'market_name': 'Test Market?',
            'edge': 0.08,
            'current_odds': 0.42,
            'side': 'YES',
            'model_confidence': 0.75
        }]
        
        actions = self.decider.plan_actions(signals)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].market_id, 'test-market')
        self.assertEqual(actions[0].side, 'YES')
        self.assertGreater(actions[0].amount, 0)
        self.assertLessEqual(actions[0].amount, 100.0)
    
    def test_plan_actions_empty(self):
        """Test with empty signals"""
        actions = self.decider.plan_actions([])
        self.assertEqual(len(actions), 0)
    
    def test_kelly_sizing_cap(self):
        """Test that Kelly sizing is capped at 10%"""
        signals = [{
            'market_id': 'test',
            'market_name': 'Test?',
            'edge': 0.50,  # Very high edge
            'current_odds': 0.5,
            'side': 'YES',
            'model_confidence': 0.90
        }]
        
        actions = self.decider.plan_actions(signals)
        
        # Should be capped at 10% of $1000 = $100
        self.assertLessEqual(actions[0].amount, 100.0)

if __name__ == '__main__':
    unittest.main()
```

#### Integration Tests

```python
# tests/test_alpha_pipeline.py
def test_full_pipeline():
    """Test complete alpha -> decider -> executor pipeline"""
    from scripts.run_pipeline import run_pipeline
    
    # Mock data or use test fixtures
    results = run_pipeline(
        bankroll=1000.0,
        dryrun=True,
        verbose=False
    )
    
    # Assertions
    assert results['success'] or 'error' in results
    if results['success']:
        assert 'steps' in results
        assert 'sync' in results['steps']
        assert 'decide' in results['steps']
        assert 'execute' in results['steps']
```

### Running Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/unit/test_decider.py -v

# Specific test case
python3 -m pytest tests/unit/test_decider.py::TestDecider::test_kelly_sizing_cap -v

# With coverage
python3 -m pytest tests/ --cov=alpha --cov=decider --cov=executor
```

---

## Adding New Features

### Feature Development Checklist

- [ ] Read relevant documentation (AI_POLICY.md, roadmap, etc.)
- [ ] Create feature branch
- [ ] Design module interface
- [ ] Write code with type hints and docstrings
- [ ] Add comprehensive tests
- [ ] Add audit logging (if applicable)
- [ ] Update API documentation
- [ ] Update architecture docs (if needed)
- [ ] Test locally
- [ ] Create pull request
- [ ] Address review feedback

### Example: Adding New Risk Metric

**1. Design Interface**:

```python
# risk/metrics.py
from typing import List

def calculate_sortino_ratio(
    returns: List[float],
    target_return: float = 0.0,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Sortino ratio focusing on downside deviation.
    
    Args:
        returns: List of period returns
        target_return: Target return threshold (default: 0.0)
        risk_free_rate: Risk-free rate (default: 0.0)
    
    Returns:
        Sortino ratio as float
    
    Example:
        >>> returns = [0.02, -0.01, 0.03, -0.02]
        >>> sortino = calculate_sortino_ratio(returns)
        >>> print(f"Sortino: {sortino:.2f}")
    """
    pass  # Implementation
```

**2. Implement with Audit Logging**:

```python
from audit import get_audit_logger
import numpy as np

audit = get_audit_logger(component="risk.metrics")

def calculate_sortino_ratio(
    returns: List[float],
    target_return: float = 0.0,
    risk_free_rate: float = 0.0
) -> float:
    # Audit the calculation
    audit.log_action(
        action_type="calculate_sortino",
        action_data={
            "num_returns": len(returns),
            "target_return": target_return
        }
    )
    
    # Calculate downside deviation
    excess_returns = [r - risk_free_rate for r in returns]
    downside_returns = [min(0, r - target_return) for r in excess_returns]
    
    mean_return = np.mean(excess_returns)
    downside_dev = np.sqrt(np.mean([r**2 for r in downside_returns]))
    
    if downside_dev == 0:
        return 0.0
    
    sortino = mean_return / downside_dev
    
    # Log result
    audit.log_decision(
        decision_type="risk_metric",
        inputs={"returns_count": len(returns)},
        outputs={"sortino_ratio": sortino}
    )
    
    return sortino
```

**3. Add Tests**:

```python
# tests/unit/test_risk_metrics.py
import unittest
from risk.metrics import calculate_sortino_ratio

class TestSortinoRatio(unittest.TestCase):
    def test_positive_returns(self):
        returns = [0.02, 0.01, 0.03, 0.02]
        sortino = calculate_sortino_ratio(returns)
        self.assertGreater(sortino, 0)
    
    def test_mixed_returns(self):
        returns = [0.02, -0.01, 0.03, -0.02]
        sortino = calculate_sortino_ratio(returns)
        self.assertIsInstance(sortino, float)
```

**4. Update Documentation**:

Add to `docs/API_REFERENCE.md`:
```markdown
##### `calculate_sortino_ratio(returns, target_return=0.0, risk_free_rate=0.0)`

Calculate Sortino ratio focusing on downside deviation.

**Parameters**:
- `returns` (List[float]): Period returns
...
```

---

## Debugging

### Enabling Debug Output

```python
# Add to module
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Processing {len(data)} items")
    # ... code ...
```

### Checking Audit Logs

```bash
# View today's audit log
tail -f logs/audit/audit_$(date +%Y-%m-%d).jsonl | jq '.'

# Filter by component
cat logs/audit/audit_2025-11-25.jsonl | jq 'select(.component == "decider")'

# Filter by session
cat logs/audit/audit_2025-11-25.jsonl | jq 'select(.session_id == "pipeline_123")'

# Count events by type
cat logs/audit/audit_2025-11-25.jsonl | jq -r '.event_type' | sort | uniq -c
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with rich traceback
from rich import traceback
traceback.install()
```

### Common Issues

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed debugging guides.

---

## Contributing

### Contribution Process

1. **Fork** repository (external contributors)
2. **Create branch** from `main`
3. **Make changes** following this guide
4. **Test thoroughly**
5. **Submit PR** with clear description
6. **Address review** feedback
7. **Merge** after approval

### Code Review Guidelines

**Reviewers check**:
- [ ] Code follows style guide
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No secrets committed
- [ ] Audit logging added (where appropriate)
- [ ] No breaking changes (or documented)

### Getting Help

- **GitHub Issues**: Ask questions, report bugs
- **Documentation**: Check all docs/ files
- **Code Comments**: Look for `# TODO` and `# FIXME`

---

## Resources

### Internal Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
- [DATA_SCHEMAS.md](DATA_SCHEMAS.md) - Data structure specifications
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [RISK_MODEL_V1.md](RISK_MODEL_V1.md) - Risk management

### External Resources

- [PEP 8](https://pep8.org/) - Python style guide
- [PEP 484](https://www.python.org/dev/peps/pep-0484/) - Type hints
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Real Python](https://realpython.com/) - Python tutorials

### Tools

- **Black**: Code formatter
- **mypy**: Static type checker
- **pytest**: Testing framework
- **jq**: JSON processor for logs

```bash
pip install black mypy pytest
```

---

## Quick Reference

### Common Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install requests openai

# Development
git checkout -b feature/my-feature
python3 -m pytest tests/ -v
python3 scripts/run_pipeline.py

# Debugging
tail -f logs/audit/audit_$(date +%Y-%m-%d).jsonl | jq '.'
cat state/polymarket-model.json | jq '.markets[0]'

# Commit
git add .
git commit -m "feat: Add new feature"
git push origin feature/my-feature
```

### File Locations

- Code: `alpha/`, `decider/`, `executor/`, `ai/`, `ai_nexus/`
- Tests: `tests/`, `tests/unit/`
- Docs: `docs/`
- State: `state/*.json`
- Logs: `logs/audit/*.jsonl`
- Config: Root level (`.gitignore`, etc.)
