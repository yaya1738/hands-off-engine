# INTEGRAFIX: Distributed Trading Architecture

## Overview

**Distributed Trading** enables your local trading implementation to seamlessly use trading components (executors, order systems, market data) housed on remote machines via the M2M infrastructure.

### What This Means

- **Local Machine**: Your primary trading computer
- **Remote Machines**: Other computers running the same trading code
- **Distributed Trading**: Ability to execute trades on ANY machine transparently

### Benefits

1. **High Availability**: If local machine fails, trades execute on remote
2. **Load Balancing**: Distribute trades across multiple machines
3. **Scalability**: Add more trading nodes as volume grows
4. **Real-Time Sync**: All machines see the same trade data
5. **Zero Code Changes**: Existing code works without modification

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Your Trading Code                          │
│  (trading_pipeline.py, trade_executor.py, etc.)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           Distributed Trading Wrapper (NEW)                  │
│  • Transparent proxy for local/remote execution              │
│  • Automatic failover and load balancing                     │
│  • Same API as local components                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌──────────────────┬──────────────────┐
        ↓                  ↓                  ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Local Node  │    │ Remote Node │    │ Remote Node │
│ (This PC)   │    │ (Server 1)  │    │ (Server 2)  │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ TradeExecutor│    │ TradeExecutor│    │ TradeExecutor│
│ Polymarket   │    │ Polymarket   │    │ Polymarket   │
│ Orders       │    │ Orders       │    │ Orders       │
└─────────────┘    └─────────────┘    └─────────────┘
        ↓                  ↓                  ↓
        └──────────────────┴──────────────────┘
                            ↓
                    Polymarket API
```

---

## Quick Start

### 1. Setup (One-Time)

On **each machine** that will run trading operations:

```bash
# Register this machine as a trading service
python3 integrafix/distributed_trading_integration.py --register --port 8080

# Output:
# 🔧 Registering local trading service...
# ✅ Registered: trading-executor-hostname-12345
#    Address: 192.168.1.100:8080
#    Node ID: trading-node-hostname-12345
```

### 2. Discover Services

From any machine, see all available trading nodes:

```bash
python3 integrafix/distributed_trading_integration.py --discover

# Output:
# 🔍 Discovering trading services...
# ✅ Found 3 service(s):
#
#    Service: trading-executor-server1-8080
#    Address: 192.168.1.100:8080
#    Local: False
#    Health: healthy
#    Capabilities: execute_trade, get_market_data, get_positions, polymarket_orders
#    Total Trades: 1,234
#    Success Rate: 98.5%
#
#    Service: trading-executor-server2-8080
#    Address: 192.168.1.101:8080
#    Local: False
#    Health: healthy
#    ...
```

### 3. Use in Your Code

**Option A: Zero Code Changes (Drop-in Replacement)**

```python
# BEFORE:
# from autonomous.trade_executor import TradeExecutor
# from executor.polymarket_orders import PolymarketOrders

# AFTER:
from integrafix.distributed_trading_wrapper import executor, orders

# SAME CODE, NOW DISTRIBUTED!
markets = executor.get_market_data(limit=20)
result = orders.limit_buy_yes('bitcoin-10k', 0.40, 10)

# If local execution fails, automatically tries remote nodes!
```

**Option B: Explicit Control**

```python
from integrafix.distributed_trading_integration import (
    get_distributed_trading,
    ExecutionMode
)

# Create proxy with specific mode
trading = get_distributed_trading(
    default_mode=ExecutionMode.LOAD_BALANCED  # Distribute across all nodes
)

# Get market data (load balanced)
result = trading.get_market_data(limit=20)

# Execute trade on remote only
result = trading.limit_buy_yes(
    'bitcoin-10k',
    0.40,
    10,
    mode=ExecutionMode.REMOTE_ONLY
)
```

---

## Execution Modes

### 1. LOCAL_ONLY
Executes only on this machine. No remote calls.

```python
from integrafix.distributed_trading_wrapper import use_local_only

use_local_only()
# Now all trades execute locally only
```

**Use When:**
- Testing local changes
- Network issues
- Don't trust remote nodes

### 2. REMOTE_ONLY
Executes only on remote machines. Never local.

```python
from integrafix.distributed_trading_wrapper import use_remote_only

use_remote_only()
# Now all trades execute remotely only
```

**Use When:**
- Local machine underpowered
- Want to use dedicated trading server
- Local environment issues

### 3. LOCAL_FIRST (Default)
Tries local first, falls back to remote on failure.

```python
# This is the default mode
from integrafix.distributed_trading_wrapper import executor, orders

# Automatic failover to remote if local fails
markets = executor.get_market_data(limit=20)
```

**Use When:**
- Want best of both worlds
- Prefer local speed, need remote reliability
- **Recommended for most scenarios**

### 4. REMOTE_FIRST
Tries remote first, falls back to local on failure.

```python
from integrafix.distributed_trading_integration import (
    get_distributed_trading,
    ExecutionMode
)

trading = get_distributed_trading(default_mode=ExecutionMode.REMOTE_FIRST)
```

**Use When:**
- Remote has better connectivity to exchange
- Remote has lower latency
- Want to offload work from local

### 5. LOAD_BALANCED
Distributes requests across all available nodes.

```python
from integrafix.distributed_trading_wrapper import use_load_balanced

use_load_balanced()
# Now trades distributed across all healthy nodes
```

**Use When:**
- High volume trading
- Want to maximize throughput
- Multiple nodes with equal capability

### 6. REDUNDANT
Executes on BOTH local AND remote for reliability.

```python
from integrafix.distributed_trading_integration import (
    get_distributed_trading,
    ExecutionMode
)

trading = get_distributed_trading(default_mode=ExecutionMode.REDUNDANT)
result = trading.limit_buy_yes('bitcoin-10k', 0.40, 10)
# Executed on both local and remote!
```

**Use When:**
- Critical trades that MUST succeed
- Want double confirmation
- **Note**: Will place order twice if both succeed!

---

## Real-Time Trade Sync

All trades are automatically published to real-time streams and synchronized across all nodes.

### Streams Available

1. **`trades`**: Real-time trade executions
   ```python
   {
       'operation': 'limit_buy_yes',
       'market': 'bitcoin-10k',
       'price': 0.40,
       'size': 10,
       'success': True,
       'executed_on': 'trading-executor-server1',
       'latency_ms': 145.2,
       'node_id': 'trading-node-server1-8080',
       'timestamp': '2025-12-05T10:30:45.123Z'
   }
   ```

2. **`market_data`**: Real-time market data updates
   ```python
   {
       'market': 'bitcoin-10k',
       'yes_price': 0.42,
       'no_price': 0.58,
       'volume': 125000
   }
   ```

3. **`positions`**: Position updates across all nodes
   ```python
   {
       'node_id': 'trading-node-server1',
       'market': 'bitcoin-10k',
       'position': 100.0,  # YES tokens
       'cost_basis': 0.40
   }
   ```

### Subscribe to Streams

```python
from autonomous.machine_stream_processor import get_processor

processor = get_processor()

def on_trade(record):
    print(f"Trade executed: {record.data}")

# Subscribe to trade stream
processor.subscribe('trades', on_trade)

# Now receives all trades from all nodes in real-time!
```

---

## Monitoring & Stats

### Check Execution Statistics

```bash
python3 integrafix/distributed_trading_integration.py --stats
```

Output:
```json
{
  "total_requests": 1234,
  "local_executions": 856,
  "remote_executions": 378,
  "failures": 0,
  "avg_latency_ms": 89.5,
  "available_services": 3,
  "local_available": true,
  "remote_available": true,
  "success_rate": 1.0
}
```

### Get Service Status

```python
from integrafix.distributed_trading_wrapper import get_service_status

services = get_service_status()
for svc in services:
    print(f"{svc['service_id']}: {svc['health']}")
    print(f"  Trades: {svc['total_trades']}")
    print(f"  Success: {svc['success_rate']:.1%}")
    print(f"  Latency: {svc['avg_latency_ms']:.1f}ms")
```

### Get Trade History

```python
from integrafix.distributed_trading_integration import get_distributed_trading

trading = get_distributed_trading()
history = trading.get_trade_history(limit=100)

for trade in history:
    print(f"{trade['timestamp']}: {trade['operation']}")
    print(f"  Result: {trade['result']['success']}")
    print(f"  Executed on: {trade['result']['executed_on']}")
```

---

## Network Setup

### Same Network (Simple)

If all machines are on the same local network (e.g., 192.168.1.x), they will automatically discover each other.

**No additional setup required!**

### Different Networks (VPN/Cloud)

If machines are on different networks, use VPN or configure service addresses manually.

**Using Tailscale VPN (Recommended):**

```bash
# Install Tailscale on all machines
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to your Tailscale network
sudo tailscale up

# Now all machines can discover each other!
```

**Manual Configuration:**

```python
from autonomous.machine_distributed_coordinator import get_coordinator

coordinator = get_coordinator()

# Manually add remote nodes
coordinator.add_cluster_node('node2', '100.64.0.2')
coordinator.add_cluster_node('node3', '100.64.0.3')
```

---

## Security

### API Key Authentication

All remote requests are authenticated via API keys (if security layer is enabled).

```python
from autonomous.machine_security import generate_api_key, Role

# Generate API key for remote trading node
api_key = generate_api_key(
    name="Remote Trading Node 2",
    role=Role.SYSTEM,  # Full system access
    rate_limit=10000   # 10k requests/hour
)

print(f"API Key: {api_key}")
# Save this key on the remote machine
```

### IP Whitelisting

Restrict which machines can execute trades:

```python
from autonomous.machine_security import get_security

security = get_security()

# Add trusted IPs
security.add_ip_to_whitelist('192.168.1.100')
security.add_ip_to_whitelist('192.168.1.101')
```

---

## Troubleshooting

### Issue: Services Not Discovered

**Check 1: Is coordinator running?**
```bash
python3 -c "from autonomous.machine_distributed_coordinator import get_coordinator; print(get_coordinator())"
```

**Check 2: Are services registered?**
```bash
python3 integrafix/distributed_trading_integration.py --discover
```

**Check 3: Network connectivity**
```bash
# From local machine, ping remote
ping 192.168.1.100

# Check if port is open
nc -zv 192.168.1.100 8080
```

### Issue: Remote Execution Fails

**Check 1: Is remote service healthy?**
```bash
# On remote machine
python3 integrafix/distributed_trading_integration.py --stats
```

**Check 2: Can local reach remote?**
```bash
# From local machine
curl http://192.168.1.100:8080/health
```

**Check 3: Check logs**
```bash
# On remote machine
tail -f logs/distributed_trading.log
```

### Issue: Trades Execute Twice

You're probably using `ExecutionMode.REDUNDANT` mode. This mode intentionally executes on both local and remote for reliability.

**Solution**: Use `LOCAL_FIRST` or `LOAD_BALANCED` instead.

---

## Performance Tuning

### Reduce Latency

1. **Use local-first mode**: Fastest when local is available
   ```python
   from integrafix.distributed_trading_wrapper import executor
   # Already default mode!
   ```

2. **Add more local services**: Run multiple local executors
   ```bash
   python3 integrafix/distributed_trading_integration.py --register --port 8080
   python3 integrafix/distributed_trading_integration.py --register --port 8081
   python3 integrafix/distributed_trading_integration.py --register --port 8082
   ```

3. **Enable Redis caching**: For coordinator and streams
   ```bash
   sudo apt install redis-server
   sudo systemctl start redis
   ```

### Increase Throughput

1. **Use load-balanced mode**: Distribute across all nodes
   ```python
   from integrafix.distributed_trading_wrapper import use_load_balanced
   use_load_balanced()
   ```

2. **Add more remote nodes**: More machines = more capacity
   ```bash
   # On each new machine
   python3 integrafix/distributed_trading_integration.py --register
   ```

3. **Optimize network**: Use wired connections, reduce latency to remote nodes

---

## Migration Guide

### Step 1: Test with Wrapper (No Code Changes)

```python
# Change this import:
# from autonomous.trade_executor import TradeExecutor

# To this:
from integrafix.distributed_trading_wrapper import executor

# All your existing code works unchanged!
markets = executor.get_market_data(limit=20)
```

### Step 2: Register Services

On each machine:
```bash
python3 integrafix/distributed_trading_integration.py --register
```

### Step 3: Verify Discovery

```bash
python3 integrafix/distributed_trading_integration.py --discover
# Should see all registered services
```

### Step 4: Test Execution

```bash
python3 integrafix/distributed_trading_integration.py --test
```

### Step 5: Monitor in Production

```bash
# Check stats regularly
python3 integrafix/distributed_trading_integration.py --stats

# Check service health
python3 integrafix/distributed_trading_wrapper.py --services
```

---

## Advanced: Custom Routing Logic

You can implement custom routing logic for specific scenarios:

```python
from integrafix.distributed_trading_integration import (
    get_distributed_trading,
    ExecutionMode
)

trading = get_distributed_trading()

def smart_route(market: str, operation: str):
    """Route trades based on market and operation."""
    # High-volume markets -> load balanced
    if market in ['bitcoin-10k', 'ethereum-5k']:
        return ExecutionMode.LOAD_BALANCED

    # Critical trades -> redundant
    if operation.startswith('market_'):
        return ExecutionMode.REDUNDANT

    # Default -> local first
    return ExecutionMode.LOCAL_FIRST

# Use custom routing
market = 'bitcoin-10k'
mode = smart_route(market, 'limit_buy_yes')
result = trading.limit_buy_yes(market, 0.40, 10, mode=mode)
```

---

## Summary

### What You Get

✅ **Transparent distributed trading** - Use remote trading components with zero code changes
✅ **Automatic failover** - If local fails, seamlessly uses remote
✅ **Load balancing** - Distribute trades across multiple machines
✅ **Real-time sync** - All nodes see same trade data in real-time
✅ **High availability** - System keeps working even if nodes fail
✅ **Scalability** - Add more nodes as volume grows
✅ **Security** - API keys, rate limiting, IP whitelisting
✅ **Monitoring** - Comprehensive stats and health checks

### Quick Reference

```bash
# Register service
python3 integrafix/distributed_trading_integration.py --register

# Discover services
python3 integrafix/distributed_trading_integration.py --discover

# Check stats
python3 integrafix/distributed_trading_integration.py --stats

# Test execution
python3 integrafix/distributed_trading_integration.py --test
```

```python
# Use distributed trading (drop-in replacement)
from integrafix.distributed_trading_wrapper import executor, orders

markets = executor.get_market_data(limit=20)
result = orders.limit_buy_yes('bitcoin-10k', 0.40, 10)
```

---

**Your local trading implementation can now use remote trading pieces seamlessly via the M2M infrastructure!** 🚀
