# Distributed Trading - Integration Guide

## How to Upgrade Your Existing Trading Code

This guide shows exactly how to update your existing INTEGRAFIX trading code to use the distributed architecture.

---

## Option 1: Drop-In Replacement (Recommended)

### For trade_executor.py Users

**Before:**
```python
from autonomous.trade_executor import TradeExecutor

executor = TradeExecutor()
markets = executor.get_market_data(limit=20)
```

**After:**
```python
from integrafix.distributed_trading_wrapper import executor

# Same code, now distributed!
markets = executor.get_market_data(limit=20)
```

**That's it!** Your code now automatically:
- Uses local executor when available
- Falls back to remote if local fails
- Load balances if configured
- Syncs trade data in real-time

---

### For polymarket_orders.py Users

**Before:**
```python
from executor.polymarket_orders import PolymarketOrders

orders = PolymarketOrders()
result = orders.limit_buy_yes('bitcoin-10k', 0.40, 10)
```

**After:**
```python
from integrafix.distributed_trading_wrapper import orders

# Same code, now distributed!
result = orders.limit_buy_yes('bitcoin-10k', 0.40, 10)
```

---

### For trading_pipeline.py

Find this code in integrafix/trading_pipeline.py:

```python
# BEFORE:
from autonomous.trade_executor import TradeExecutor
from executor.polymarket_orders import PolymarketOrders

class TradingPipeline:
    def __init__(self):
        self.executor = TradeExecutor()
        self.orders = PolymarketOrders()
```

Change to:

```python
# AFTER:
from integrafix.distributed_trading_wrapper import executor, orders

class TradingPipeline:
    def __init__(self):
        self.executor = executor  # Now distributed!
        self.orders = orders      # Now distributed!
```

**All your existing trading logic continues to work unchanged!**

---

## Option 2: Explicit Control (Advanced)

If you want explicit control over execution mode:

```python
from integrafix.distributed_trading_integration import (
    get_distributed_trading,
    ExecutionMode
)

# Create trading proxy with specific mode
trading = get_distributed_trading(
    default_mode=ExecutionMode.LOAD_BALANCED
)

# Execute with explicit mode
result = trading.get_market_data(
    limit=20,
    mode=ExecutionMode.LOCAL_FIRST
)

# Place order with specific mode
result = trading.limit_buy_yes(
    market='bitcoin-10k',
    price=0.40,
    size=10,
    mode=ExecutionMode.REMOTE_FIRST
)

# Get detailed stats
stats = trading.get_stats()
print(f"Local: {stats['local_executions']}")
print(f"Remote: {stats['remote_executions']}")
print(f"Success Rate: {stats['success_rate']:.1%}")
```

---

## Specific File Updates

### 1. autonomous/trade_executor.py

**If you import TradeExecutor in other files:**

```python
# Find all files with this import:
grep -r "from autonomous.trade_executor import TradeExecutor" .

# Replace with:
from integrafix.distributed_trading_wrapper import executor
# Then use 'executor' directly instead of 'TradeExecutor()'
```

**Example:**
```python
# Before:
from autonomous.trade_executor import TradeExecutor
executor = TradeExecutor()
markets = executor.get_market_data()

# After:
from integrafix.distributed_trading_wrapper import executor
markets = executor.get_market_data()
```

### 2. executor/polymarket_orders.py

**If you import PolymarketOrders in other files:**

```python
# Find all files with this import:
grep -r "from executor.polymarket_orders import PolymarketOrders" .

# Replace with:
from integrafix.distributed_trading_wrapper import orders
# Then use 'orders' directly instead of 'PolymarketOrders()'
```

**Example:**
```python
# Before:
from executor.polymarket_orders import PolymarketOrders
orders = PolymarketOrders()
result = orders.limit_buy_yes('market', 0.40, 10)

# After:
from integrafix.distributed_trading_wrapper import orders
result = orders.limit_buy_yes('market', 0.40, 10)
```

### 3. integrafix/trading_pipeline.py

**Update the TradingPipeline class:**

```python
# At the top of the file, change:
# from autonomous.trade_executor import TradeExecutor
# from executor.polymarket_orders import PolymarketOrders

# To:
from integrafix.distributed_trading_wrapper import executor, orders

# In __init__ method, change:
# self.executor = TradeExecutor()
# self.orders = PolymarketOrders()

# To:
self.executor = executor
self.orders = orders
```

### 4. autonomous/concrete_executor.py

If this file uses trading components:

```python
# Change:
# from autonomous.trade_executor import TradeExecutor

# To:
from integrafix.distributed_trading_wrapper import executor

# Then replace:
# executor = TradeExecutor()

# With:
# executor is already initialized, just use it
```

---

## Testing Your Changes

### 1. Test Local Execution

```bash
# Ensure local execution still works
python3 -c "
from integrafix.distributed_trading_wrapper import executor
markets = executor.get_market_data(limit=5)
print(f'✅ Fetched {len(markets)} markets')
"
```

Expected output:
```
✅ Fetched 5 markets
```

### 2. Test Wrapper Integration

```bash
python3 integrafix/distributed_trading_wrapper.py --test
```

Expected output:
```
🧪 Testing distributed trading wrapper...
1. Getting market data...
   ✅ Received 5 markets
✅ Test complete
```

### 3. Test Your Trading Pipeline

```bash
# Run your actual trading code
python3 integrafix/trading_pipeline.py
# Or whatever your entry point is
```

---

## Setting Up Remote Nodes

Once your local code is updated, set up remote nodes:

### On Remote Machine 1:

```bash
# Clone repo
git clone <your-repo> && cd hands-off-engine

# Register as trading service
python3 integrafix/distributed_trading_integration.py --register --port 8080
```

### On Remote Machine 2:

```bash
# Clone repo
git clone <your-repo> && cd hands-off-engine

# Register as trading service
python3 integrafix/distributed_trading_integration.py --register --port 8080
```

### Verify Discovery (from local machine):

```bash
python3 integrafix/distributed_trading_integration.py --discover
```

Expected output:
```
🔍 Discovering trading services...

✅ Found 3 service(s):

   Service: trading-executor-local-8080
   Address: 192.168.1.100:8080
   Local: True
   Health: healthy

   Service: trading-executor-remote1-8080
   Address: 192.168.1.101:8080
   Local: False
   Health: healthy

   Service: trading-executor-remote2-8080
   Address: 192.168.1.102:8080
   Local: False
   Health: healthy
```

---

## Monitoring

### Check Execution Stats

```python
from integrafix.distributed_trading_wrapper import get_trading_stats

stats = get_trading_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Local executions: {stats['local_executions']}")
print(f"Remote executions: {stats['remote_executions']}")
print(f"Success rate: {stats['success_rate']:.1%}")
```

### Check Service Status

```python
from integrafix.distributed_trading_wrapper import get_service_status

services = get_service_status()
for svc in services:
    print(f"{svc['service_id']}:")
    print(f"  Health: {svc['health']}")
    print(f"  Total Trades: {svc['total_trades']}")
    print(f"  Success Rate: {svc['success_rate']:.1%}")
```

---

## Switching Execution Modes

### Use Local Only (for testing)

```python
from integrafix.distributed_trading_wrapper import use_local_only

use_local_only()
# Now all trades execute locally only
```

### Use Load Balanced (for high volume)

```python
from integrafix.distributed_trading_wrapper import use_load_balanced

use_load_balanced()
# Now trades distributed across all nodes
```

### Use Remote Only (to offload work)

```python
from integrafix.distributed_trading_wrapper import use_remote_only

use_remote_only()
# Now all trades execute remotely only
```

---

## Rollback Plan

If you need to rollback to local-only execution:

### Option 1: Change Imports Back

```python
# Change back to:
from autonomous.trade_executor import TradeExecutor
from executor.polymarket_orders import PolymarketOrders

executor = TradeExecutor()
orders = PolymarketOrders()
```

### Option 2: Use Local-Only Mode

```python
# Keep distributed imports but use local-only mode:
from integrafix.distributed_trading_wrapper import use_local_only

use_local_only()
# Now behaves like local-only, but infrastructure still available
```

---

## Troubleshooting

### Issue: "No module named 'integrafix.distributed_trading_wrapper'"

**Fix:**
```bash
# Ensure you're in project root
cd /root/hands-off-engine

# Verify file exists
ls -l integrafix/distributed_trading_wrapper.py
```

### Issue: "Distributed coordinator not available"

**Fix:**
This is a warning, not an error. The system falls back to local execution without coordinator features (service discovery, load balancing). To enable full distributed features, ensure M2M components are available.

### Issue: Remote services not discovered

**Fix:**
1. Check network connectivity:
   ```bash
   ping <remote-ip>
   ```

2. Verify remote service is registered:
   ```bash
   # On remote machine
   python3 integrafix/distributed_trading_integration.py --stats
   ```

3. Check firewall:
   ```bash
   # Ensure port 8080 is open
   sudo ufw allow 8080
   ```

---

## Summary

**Minimal changes required:**

1. **Change imports** (1 line per file):
   ```python
   from integrafix.distributed_trading_wrapper import executor, orders
   ```

2. **Use directly** (no initialization needed):
   ```python
   markets = executor.get_market_data(limit=20)
   result = orders.limit_buy_yes('bitcoin-10k', 0.40, 10)
   ```

3. **Setup remote nodes** (optional):
   ```bash
   python3 integrafix/distributed_trading_integration.py --register
   ```

**That's it! Your trading system is now distributed with automatic failover and load balancing.**

---

Serving: Yair Siegel
