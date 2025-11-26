# Troubleshooting Guide

Common issues, error messages, debugging procedures, and recovery strategies for the Hands-Off Engine.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Common Error Messages](#common-error-messages)
3. [Module-Specific Issues](#module-specific-issues)
4. [Debugging Procedures](#debugging-procedures)
5. [Recovery Procedures](#recovery-procedures)
6. [Performance Issues](#performance-issues)
7. [FAQ](#faq)

---

## Quick Diagnosis

### System Health Check

Run this quick diagnostic script:

```bash
#!/bin/bash
echo "=== Hands-Off Engine Health Check ==="

echo "\n1. Python Version:"
python3 --version

echo "\n2. Required Files:"
for file in state/knowledge.json state/polymarket-model.json; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done

echo "\n3. Directory Structure:"
for dir in alpha decider executor audit state logs; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/ exists"
    else
        echo "✗ $dir/ missing"
    fi
done

echo "\n4. Recent Audit Logs:"
if [ -d "logs/audit" ]; then
    ls -lht logs/audit/ | head -5
else
    echo "✗ No audit logs directory"
fi

echo "\n5. State File Timestamps:"
ls -lh state/*.json 2>/dev/null | tail -5

echo "\n=== Health Check Complete ==="
```

Save as `scripts/health_check.sh` and run:
```bash
bash scripts/health_check.sh
```

---

## Common Error Messages

### `FileNotFoundError: polymarket-compact.json not found`

**Symptom**:
```
FileNotFoundError: Input file not found: termux-hands-off/out/polymarket-compact.json
```

**Cause**: Input data file doesn't exist.

**Solution**:

1. **Check if file exists**:
   ```bash
   ls -l termux-hands-off/out/polymarket-compact.json
   ```

2. **Create test data** (for development):
   ```bash
   mkdir -p termux-hands-off/out
   cat > termux-hands-off/out/polymarket-compact.json << 'EOF'
   {
     "timestamp": "2025-11-25T12:00:00Z",
     "markets": {
       "crypto": [
         {
           "slug": "btc-100k-2024",
           "question": "Will Bitcoin reach $100k in 2024?",
           "last": 0.35,
           "bestBid": 0.34,
           "bestAsk": 0.36,
           "volume24h": 50000.0
         }
       ]
     }
   }
   EOF
   ```

3. **Run pipeline again**:
   ```bash
   python3 scripts/run_pipeline.py
   ```

---

### `ModuleNotFoundError: No module named 'audit'`

**Symptom**:
```python
ModuleNotFoundError: No module named 'audit'
```

**Cause**: Python can't find the audit module (path issue).

**Solution**:

1. **Check current directory**:
   ```bash
   pwd  # Should be in repo root
   ls audit/  # Should see audit_logger.py
   ```

2. **Run from repo root**:
   ```bash
   cd /path/to/hands-off-engine
   python3 scripts/run_pipeline.py
   ```

3. **Check `__init__.py` exists**:
   ```bash
   ls audit/__init__.py
   # If missing, create it:
   touch audit/__init__.py
   ```

---

### `JSONDecodeError: Expecting value`

**Symptom**:
```python
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause**: JSON file is empty or corrupted.

**Solution**:

1. **Check file content**:
   ```bash
   cat state/polymarket-model.json
   # or
   head -20 state/polymarket-model.json
   ```

2. **Validate JSON**:
   ```bash
   python3 -m json.tool state/polymarket-model.json
   ```

3. **Restore from backup** (if available):
   ```bash
   cp state/polymarket-model.json.bak state/polymarket-model.json
   ```

4. **Regenerate**:
   ```bash
   python3 alpha/sync_polymarket_model.py
   ```

---

### `PermissionError: [Errno 13] Permission denied`

**Symptom**:
```python
PermissionError: [Errno 13] Permission denied: 'logs/audit/audit_2025-11-25.jsonl'
```

**Cause**: No write permissions for log directory.

**Solution**:

1. **Check permissions**:
   ```bash
   ls -la logs/audit/
   ```

2. **Fix permissions**:
   ```bash
   chmod 755 logs/audit
   chmod 644 logs/audit/*.jsonl
   ```

3. **Check disk space**:
   ```bash
   df -h .
   ```

---

### `KeyError: 'markets'`

**Symptom**:
```python
KeyError: 'markets'
```

**Cause**: Expected key missing from JSON data.

**Solution**:

1. **Inspect data structure**:
   ```bash
   cat state/polymarket-model.json | jq 'keys'
   ```

2. **Check schema** (see [DATA_SCHEMAS.md](DATA_SCHEMAS.md))

3. **Validate with Python**:
   ```python
   import json
   with open('state/polymarket-model.json', 'r') as f:
       data = json.load(f)
       print(data.keys())
       if 'markets' in data:
           print(f"Found {len(data['markets'])} markets")
   ```

---

## Module-Specific Issues

### Alpha Module Issues

#### Issue: No markets selected

**Symptom**:
```
Markets analyzed: 100
Markets selected: 0
```

**Cause**: All markets filtered out (edge too low, prices too extreme).

**Debug**:
```python
python3 alpha/sync_polymarket_model.py
```

Check output for filtering reasons.

**Solution**:

1. **Lower edge threshold** (temporary for testing):
   ```python
   # alpha/sync_polymarket_model.py
   # Change line ~154:
   if edge < 0.03:  # Was 0.05
       return None
   ```

2. **Check market data quality**:
   ```bash
   cat termux-hands-off/out/polymarket-compact.json | jq '.markets | to_entries | .[0].value[0]'
   ```

#### Issue: Fair price estimation seems wrong

**Symptom**: All fair prices are nearly identical to market prices.

**Cause**: Placeholder estimation algorithm is too simple.

**Solution**: This is expected. The `estimate_fair_price()` function uses a simple heuristic:

```python
# This is a PLACEHOLDER - in production, use sophisticated models
fair = (best_bid + last) / 2.0 + small_adjustment
```

To improve:
1. Integrate real alpha model
2. Use historical data
3. Apply machine learning

---

### Decider Module Issues

#### Issue: Position sizes all capped at $100

**Symptom**: Every position is exactly $100.

**Cause**: Kelly calculation exceeds 10% cap, which is then capped at MAX_POSITION_SIZE.

**Debug**:
```python
from decider.ho_decider import Decider

decider = Decider(bankroll=1000.0)
signals = [...]  # Your signals

actions = decider.plan_actions(signals)
for action in actions:
    print(f"{action.market_name}:")
    print(f"  Amount: ${action.amount:.2f}")
    print(f"  Confidence: {action.confidence:.1%}")
    print(f"  Reasoning: {action.reasoning}")
```

**Solution**: This is correct behavior per RISK_MODEL_V1.md:
- Max 10% of bankroll per position
- Absolute cap at $100

To adjust (not recommended):
```python
# decider/ho_decider.py
max_fraction = 0.15  # Increase to 15% (RISKY!)
```

#### Issue: `TypeError: 'NoneType' object is not subscriptable`

**Symptom**:
```python
TypeError: 'NoneType' object is not subscriptable
```

**Cause**: Missing required field in signal dict.

**Debug**:
```python
signals = decider.load_model_signals(Path('state/polymarket-model.json'))
print(signals[0].keys())  # Check what keys exist
```

**Solution**: Ensure all required fields present:
```python
required_fields = ['market_id', 'market_name', 'edge', 'side']
for signal in signals:
    for field in required_fields:
        if field not in signal:
            print(f"Missing field '{field}' in {signal.get('market_id', 'unknown')}")
```

---

### Executor Module Issues

#### Issue: All actions rejected

**Symptom**:
```
Successful: 0/10
Rejected: 10
```

**Cause**: Actions failing validation checks.

**Debug**:
```python
from executor.ho_executor_plan import Executor

executor = Executor(dryrun=True)
for action in actions:
    is_valid, msg = executor.validate_action(action)
    if not is_valid:
        print(f"Rejected: {action.market_name}")
        print(f"  Reason: {msg}")
```

**Common Rejection Reasons**:

1. **Low confidence** (< 70%):
   ```
   Confidence 65.0% below threshold 70.0%
   ```
   
   **Solution**: This is correct behavior. Increase model confidence or lower threshold (not recommended).

2. **Position too large** (> $100):
   ```
   Position size $150.00 exceeds max $100.00
   ```
   
   **Solution**: Reduce bankroll or adjust sizing logic in Decider.

3. **Invalid side**:
   ```
   Invalid side 'BUY', must be YES or NO
   ```
   
   **Solution**: Fix data pipeline - side must be "YES" or "NO".

---

### Audit Module Issues

#### Issue: Audit logs not being created

**Symptom**: No files in `logs/audit/` directory.

**Debug**:
```python
from audit import get_audit_logger

audit = get_audit_logger(component="test")
audit.log_action(
    action_type="test",
    action_data={"test": "value"}
)
print(f"Log directory: {audit.log_dir}")
print(f"Log file: {audit._log_file}")
```

**Solution**:

1. **Check directory exists**:
   ```bash
   mkdir -p logs/audit
   ```

2. **Check permissions**:
   ```bash
   chmod 755 logs/audit
   ```

3. **Check disk space**:
   ```bash
   df -h logs/audit
   ```

4. **Check stderr** (fallback location):
   ```bash
   python3 your_script.py 2>&1 | grep "AUDIT"
   ```

#### Issue: Audit log file corruption

**Symptom**: Can't parse audit log as JSONL.

**Solution**:

1. **Identify corrupt lines**:
   ```bash
   cat logs/audit/audit_2025-11-25.jsonl | while read line; do
       echo "$line" | jq '.' > /dev/null 2>&1 || echo "Corrupt: $line"
   done
   ```

2. **Fix manually** or **skip corrupt lines**:
   ```python
   import json
   
   with open('logs/audit/audit_2025-11-25.jsonl', 'r') as f:
       for i, line in enumerate(f, 1):
           try:
               event = json.loads(line)
               # Process event
           except json.JSONDecodeError as e:
               print(f"Line {i} corrupt: {e}")
               continue
   ```

---

## Debugging Procedures

### Step-by-Step Pipeline Debugging

#### 1. Isolate the Issue

Run each step independently:

```bash
# Step 1: Alpha sync
python3 alpha/sync_polymarket_model.py

# Step 2: Check output
cat state/polymarket-model.json | jq '.markets_selected'

# Step 3: Test Decider
python3 -c "
from decider.ho_decider import Decider
from pathlib import Path

decider = Decider(bankroll=1000.0)
signals = decider.load_model_signals(Path('state/polymarket-model.json'))
print(f'Loaded {len(signals)} signals')

actions = decider.plan_actions(signals)
print(f'Planned {len(actions)} actions')
"

# Step 4: Test Executor
python3 -c "
from executor.ho_executor_plan import Executor
from decider.ho_decider import Decider
from pathlib import Path

decider = Decider(bankroll=1000.0)
signals = decider.load_model_signals(Path('state/polymarket-model.json'))
actions = decider.plan_actions(signals)

executor = Executor(dryrun=True)
results = executor.execute_actions(actions)

summary = executor.get_execution_summary(results)
print(f'Executed: {summary[\"successful\"]}/{summary[\"total_actions\"]}')
"
```

#### 2. Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Run your code
```

#### 3. Inspect Audit Trail

```bash
# View session
SESSION_ID="pipeline_20251125_120000"
cat logs/audit/audit_2025-11-25.jsonl | \
    jq "select(.session_id == \"$SESSION_ID\")" | \
    jq -s 'sort_by(.timestamp)'

# View by component
cat logs/audit/audit_2025-11-25.jsonl | \
    jq 'select(.component == "decider")' | less
```

#### 4. Check State Files

```bash
# Validate state files
for file in state/*.json; do
    echo "Checking $file..."
    python3 -m json.tool "$file" > /dev/null && echo "  ✓ Valid JSON" || echo "  ✗ Invalid JSON"
done

# Check timestamps
ls -lht state/*.json
```

---

### Interactive Debugging

#### Using Python Debugger (pdb)

```python
# Add to code where you want to pause
import pdb; pdb.set_trace()

# Or on exception
import pdb, sys
try:
    # Your code
    risky_operation()
except:
    pdb.post_mortem(sys.exc_info()[2])
```

**PDB Commands**:
- `n`: Next line
- `s`: Step into function
- `c`: Continue execution
- `p variable`: Print variable
- `l`: List source code
- `q`: Quit debugger

#### Using IPython

```bash
pip install ipython

ipython
```

```python
In [1]: from decider.ho_decider import Decider

In [2]: decider = Decider(bankroll=1000.0)

In [3]: # Interactive exploration
   ...: decider.bankroll
Out[3]: 1000.0

In [4]: # Tab completion works
   ...: decider.<TAB>
```

---

## Recovery Procedures

### Corrupted State File Recovery

#### Scenario: `polymarket-model.json` corrupted

**Symptoms**: JSON parse errors, missing data, truncated file.

**Recovery Steps**:

1. **Check if `.tmp` file exists**:
   ```bash
   ls -l state/polymarket-model.json.tmp
   ```
   
   If it exists and is valid:
   ```bash
   mv state/polymarket-model.json.tmp state/polymarket-model.json
   ```

2. **Restore from git** (if committed):
   ```bash
   git checkout state/polymarket-model.json
   ```

3. **Regenerate**:
   ```bash
   python3 alpha/sync_polymarket_model.py
   ```

4. **Use minimal valid structure** (last resort):
   ```bash
   cat > state/polymarket-model.json << 'EOF'
   {
     "generated_at": "2025-11-25T12:00:00Z",
     "source_timestamp": "2025-11-25T12:00:00Z",
     "total_markets_analyzed": 0,
     "markets_selected": 0,
     "markets": []
   }
   EOF
   ```

---

### Lost Audit Logs Recovery

**Scenario**: Audit logs deleted or corrupted.

**Impact**: Loss of historical audit trail (can't reconstruct past decisions).

**Prevention**:
```bash
# Regular backups
mkdir -p ~/hands-off-backups/audit
cp logs/audit/*.jsonl ~/hands-off-backups/audit/

# Compress old logs
find logs/audit -name "*.jsonl" -mtime +30 -exec gzip {} \;
```

**Partial Recovery**:

1. **Check git history**:
   ```bash
   git log --all --full-history logs/audit/
   ```

2. **Reconstruct from state files** (limited):
   ```bash
   # Can recover final states but not the full trail
   git log --all --oneline -- state/
   ```

---

### Rollback After Failed Update

**Scenario**: Code update broke the system.

**Recovery**:

1. **Identify last working commit**:
   ```bash
   git log --oneline -10
   ```

2. **Rollback**:
   ```bash
   git checkout <last-working-commit>
   ```

3. **Test**:
   ```bash
   python3 scripts/run_pipeline.py
   ```

4. **Fix forward** (preferred):
   ```bash
   git checkout main
   git revert <bad-commit>
   ```

---

## Performance Issues

### Slow Pipeline Execution

**Symptom**: Pipeline takes > 30 seconds to complete.

**Debug**:

```python
import time
from scripts.run_pipeline import run_pipeline

start = time.time()
results = run_pipeline(bankroll=1000.0, dryrun=True, verbose=True)
duration = time.time() - start

print(f"Total duration: {duration:.2f}s")
```

**Common Causes**:

1. **Large input file**:
   - **Solution**: Filter markets before processing
   - **Optimize**: Use streaming JSON parser

2. **Slow disk I/O**:
   - **Check**: `iostat -x 1`
   - **Solution**: Use SSD, reduce log verbosity

3. **Network latency** (if fetching data):
   - **Solution**: Cache data locally, reduce API calls

### High Memory Usage

**Debug**:
```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**Solutions**:
1. Process markets in batches
2. Use generators instead of lists
3. Clear large objects after use

---

## FAQ

### Q: How do I enable LIVE trading mode?

**A**: LIVE mode requires explicit approval and should only be enabled after thorough DRYRUN validation.

**DO NOT** enable LIVE mode unless:
- ✓ 2+ weeks of DRYRUN with positive results
- ✓ Audit logs reviewed
- ✓ Risk model validated
- ✓ User explicitly approves

To enable (when ready):
```python
# executor/ho_executor_plan.py
executor = Executor(dryrun=False)  # CAUTION: Real capital at risk!
```

---

### Q: Why are all my positions rejected?

**A**: Likely failing confidence threshold (70%) or size limit ($100).

Check rejection reasons:
```python
from executor.ho_executor_plan import Executor

executor = Executor()
for action in actions:
    is_valid, msg = executor.validate_action(action)
    print(f"{action.market_name}: {msg}")
```

---

### Q: Can I change the risk parameters?

**A**: Yes, but **not recommended** until V1 is proven stable.

See `docs/RISK_MODEL_V1.md` for current parameters.

To change (use caution):
```python
# executor/ho_executor_plan.py
MAX_POSITION_SIZE = 50.0  # Reduce from $100
MIN_CONFIDENCE_THRESHOLD = 0.60  # Lower from 70% (RISKY!)

# decider/ho_decider.py
max_fraction = 0.05  # Reduce from 10% of bankroll
```

---

### Q: How do I view audit logs in human-readable format?

**A**: Use `jq` for pretty printing:

```bash
# Pretty print entire log
cat logs/audit/audit_2025-11-25.jsonl | jq '.'

# Filter by event type
cat logs/audit/audit_2025-11-25.jsonl | jq 'select(.event_type == "decision")'

# Show only key fields
cat logs/audit/audit_2025-11-25.jsonl | jq '{timestamp, component, event_type, data}'

# Create HTML report (advanced)
cat logs/audit/audit_2025-11-25.jsonl | jq -s '.' | jq -r '@html'
```

---

### Q: Pipeline works locally but fails on server?

**A**: Common causes:

1. **Different Python version**:
   ```bash
   python3 --version  # Check version matches
   ```

2. **Missing dependencies**:
   ```bash
   pip install -r requirements.txt  # If exists
   ```

3. **Path differences**:
   ```python
   # Use absolute paths
   from pathlib import Path
   repo_root = Path(__file__).parent.parent
   ```

4. **Permissions**:
   ```bash
   chmod -R 755 scripts/
   chmod 644 state/*.json
   ```

---

### Q: How do I reset everything to a clean state?

**A**: 

```bash
# CAUTION: This deletes all state and logs!

# Backup first
mkdir -p ~/hands-off-backup
cp -r state logs ~/hands-off-backup/

# Clean
rm state/*.json
rm logs/audit/*.jsonl

# Reinitialize
mkdir -p logs/audit
cat > state/knowledge.json << 'EOF'
{
  "primary_status_doc": "termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md",
  "ai_bootstrap_instructions": [
    "Read the primary_status_doc before planning or changing anything."
  ]
}
EOF

# Test
python3 scripts/run_pipeline.py
```

---

### Q: What should I do if I find a bug?

**A**:

1. **Check if it's already known**: See existing GitHub Issues
2. **Reproduce minimally**: Create smallest test case
3. **Check audit logs**: Look for error events
4. **Report**:
   ```markdown
   ## Bug Report
   
   **Description**: Brief description
   
   **Steps to Reproduce**:
   1. Step 1
   2. Step 2
   
   **Expected**: What should happen
   
   **Actual**: What actually happens
   
   **Environment**:
   - Python version: 3.12.3
   - OS: Ubuntu 22.04
   
   **Logs**: Relevant audit log excerpts
   ```

---

## Emergency Contacts

### Critical Issues

For production-critical issues:

1. **Check system status**: 
   ```bash
   bash scripts/health_check.sh
   ```

2. **Stop all automated processes**:
   ```bash
   # Kill any running pipelines
   pkill -f run_pipeline.py
   ```

3. **Switch to DRYRUN** (if in LIVE mode):
   ```python
   # Emergency: force DRYRUN
   executor = Executor(dryrun=True)
   ```

4. **Preserve state**:
   ```bash
   # Backup everything
   tar -czf emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz state/ logs/
   ```

5. **Report via Telegram** (primary channel) or GitHub Issues

---

## Additional Resources

- [API_REFERENCE.md](API_REFERENCE.md) - Function signatures and usage
- [DATA_SCHEMAS.md](DATA_SCHEMAS.md) - Data formats
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development workflows
- [RISK_MODEL_V1.md](RISK_MODEL_V1.md) - Risk parameters

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-26 | Initial troubleshooting guide |
