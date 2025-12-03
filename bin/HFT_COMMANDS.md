# HFT Commands Quick Reference

## One-Liner Commands

```bash
# Add to PATH (run once)
export PATH="/root/hands-off-engine/bin:$PATH"

# Or use full path
/root/hands-off-engine/bin/ho-hft status
```

## ho-hft - HFT Operations

```bash
ho-hft status              # Fleet status & capacity
ho-hft benchmark           # Throughput benchmark
ho-hft wallets             # List wallets
ho-hft wallets create 100  # Create 100 wallets
ho-hft presign TOKEN 0.5   # Pre-sign at price 0.5
ho-hft fire TOKEN 1000     # Fire 1000 orders
ho-hft start               # Start HFT processes
ho-hft stop                # Stop HFT processes
ho-hft orders              # Current orders
ho-hft cancel-all          # Cancel everything
```

## ho-fleet - Wallet Fleet

```bash
ho-fleet status    # Overview
ho-fleet create 10 # Create wallets
ho-fleet list      # List wallets
ho-fleet orders    # All orders
ho-fleet cancel    # Cancel all
ho-fleet balance   # Check balances
```

## Direct Python (for scripts/cron)

```bash
# Status
PYTHONPATH=/root/hands-off-engine python3 -c "
from executor.hft_million_coordinator import HFTMillionCoordinator
c = HFTMillionCoordinator()
print(c.calculate_capacity())
"

# Create wallets
PYTHONPATH=/root/hands-off-engine python3 -c "
from executor.multi_wallet_manager import MultiWalletManager
m = MultiWalletManager()
m.create_wallet_batch(10, 'auto')
"

# Fire orders
PYTHONPATH=/root/hands-off-engine python3 -c "
import asyncio
from executor.hft_order_cannon import HFTOrderCannon
async def fire():
    c = HFTOrderCannon()
    r = await c.fire_barrage([{'test': i} for i in range(100)])
    print(r)
    await c.cleanup()
asyncio.run(fire())
"
```

## Scaling to 1M Orders/Sec

```bash
# Step 1: Create wallet fleet
ho-hft wallets create 1000

# Step 2: Pre-sign orders
ho-hft presign YOUR_TOKEN_ID 0.5 100

# Step 3: Start fleet
ho-hft start

# Step 4: Fire at will
ho-hft fire YOUR_TOKEN_ID 10000
```

## File Locations

```
bin/
  ho-hft              # HFT command center
  ho-fleet            # Wallet fleet manager
  HFT_COMMANDS.md     # This file

executor/
  hft_million_coordinator.py   # 1M+/sec orchestrator
  hft_order_cannon.py          # Async HTTP cannon
  hft_order_presigner.py       # Pre-sign orders
  rapid_order_manager.py       # Batch operations
  multi_wallet_manager.py      # Wallet creation
  parallel_order_orchestrator.py # Multi-wallet orders
  wallet_flow_coordinator.py   # Cross-wallet transfers
  fleet_commander.py           # Multi-process fleet

state/wallets/
  registry.json       # Wallet registry
```

## On Droplets

```bash
# SSH to droplet and run
ssh root@DROPLET_IP
cd /root/hands-off-engine
export PATH="$PWD/bin:$PATH"
ho-hft status
```
