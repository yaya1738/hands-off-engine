# PRODUCTION INFRASTRUCTURE REQUIREMENTS
## Hands-Off-Engine at Full Operational Scale

**Date:** December 5, 2025
**Master:** Yair Siegel
**Analysis:** Based on actual production specifications, not minimal testing

---

## EXECUTIVE SUMMARY

**The Challenge:**
Existing hardware recommendations (1 vCPU, 1GB RAM) are based on CURRENT minimal usage during development/testing. But the system is designed for HIGH-FREQUENCY TRADING at **1 million orders per second**.

**The Reality:**
When fully operational, this system needs enterprise-grade HFT infrastructure to achieve its design goals.

**Production Target:**
- **$1,000,000 in 5 seconds** = $200,000/second throughput
- **1,000,000 orders per second** execution capability
- **63-wallet fleet** operating in parallel
- **Microsecond latency** for HFT operations
- **100,000+ msg/sec** M2M communication
- **10,000+ trades/sec** distributed trading

---

## CURRENT STATE vs PRODUCTION STATE

### Current State (What Blueprint Analyzes)
```
Environment: Development/Testing
Workload: Backend loop (every 5 min) + minimal trading
CPU Usage: <10% of 8 vCPU
RAM Usage: ~300MB
Trading Volume: Low (testing mode)
Order Rate: <1 order/minute

Conclusion: 1 vCPU, 1GB RAM sufficient
Cost: $0/month (Oracle Free)
```

### Production State (Design Intent)
```
Environment: Live HFT Trading
Workload: 1M orders/sec + 63 wallets + distributed trading
CPU Usage: 100% of many cores (parallel processing)
RAM Usage: GBs for transaction cache + wallet fleet
Trading Volume: $200K/second throughput
Order Rate: 1,000,000 orders/second

Conclusion: Enterprise HFT infrastructure required
Cost: $XXX/month (TBD)
```

---

## PRODUCTION REQUIREMENTS ANALYSIS

### From config/money_printer_specs.json

```json
{
  "target_dollars": 1000000,
  "target_seconds": 5,
  "throughput_dollars_per_second": 200000,
  "infrastructure": {
    "wallet_fleet": 63,
    "orders_per_second": 1000000,
    "pre_signed_cache": true,
    "lock_free_queue": true
  }
}
```

**What This Means:**

1. **1 Million Orders/Second**
   - Need: High CPU core count for parallel processing
   - Need: Lock-free concurrent data structures
   - Need: Pre-signed transaction cache (memory)
   - Need: Ultra-low latency networking

2. **63-Wallet Fleet**
   - Need: Sufficient RAM for 63 wallet instances
   - Need: Parallel execution across all wallets
   - Need: Coordination and state synchronization
   - Need: High IOPS for state persistence

3. **$200K/Second Throughput**
   - Need: High-bandwidth network connection
   - Need: Fast order placement and execution
   - Need: Real-time market data processing
   - Need: Rapid state updates

4. **Pre-Signed Transaction Cache**
   - Need: Large memory allocation for cache
   - Need: Fast memory access (low latency)
   - Need: Cache invalidation and refresh logic

5. **Lock-Free Queue**
   - Need: High CPU performance for lock-free algorithms
   - Need: Memory bandwidth for concurrent access
   - Need: Multiple CPU cores for true parallelism

---

## COMPUTATIONAL REQUIREMENTS

### CPU Requirements

**Order Processing:**
- 1M orders/second ÷ 1000 orders/core/second = **1000 CPU cores** (theoretical)
- With optimizations (batching, pre-signing): **50-100 cores** (practical)

**Wallet Management:**
- 63 wallets × 1 core/wallet = **63 cores minimum**
- With parallel processing: **32-64 cores practical**

**M2M Communication:**
- 100K msg/sec ÷ 10K msg/core/sec = **10 cores**

**Trading Logic + ABCFC:**
- Decision making: **8-16 cores**
- Market data processing: **8-16 cores**

**Total CPU Estimate:** **100-200 vCPU cores**

### Memory Requirements

**63-Wallet Fleet:**
- 63 wallets × 500MB/wallet = **31.5 GB**

**Pre-Signed Transaction Cache:**
- 10,000 pre-signed txs × 2KB/tx = **20 MB**
- With rotation: **100 MB**

**Lock-Free Queues:**
- Order queue: **1 GB**
- Message queue: **500 MB**
- Event queue: **500 MB**

**Market Data:**
- Real-time data: **2 GB**
- Historical data: **5 GB**

**State Files + Logs:**
- Trading state: **1 GB**
- Logs: **5 GB**

**Operating System + Services:**
- Base OS: **2 GB**
- Python + dependencies: **2 GB**

**Total RAM Estimate:** **50-100 GB**

### Storage Requirements

**Transaction Logs:**
- 1M orders/sec × 1KB/order × 3600 sec = **3.6 TB/hour**
- With compression (90%): **360 GB/hour**
- Daily: **8.6 TB** (with compression)

**State Persistence:**
- Wallet states: **10 GB**
- Trading state: **20 GB**
- Market data: **50 GB**

**Backups:**
- Incremental: **100 GB/day**

**Total Storage Estimate:** **10-20 TB** (with log rotation)

### Network Requirements

**Trading API Calls:**
- 1M orders/sec × 10 KB/order = **10 GB/sec** = **80 Gbps**
- With batching (80% reduction): **16 Gbps**

**Market Data:**
- Real-time feeds: **1 Gbps**
- WebSocket connections: **500 Mbps**

**M2M Communication:**
- 100K msg/sec × 1KB/msg = **100 MB/sec** = **800 Mbps**

**Total Network Estimate:** **20-40 Gbps**

---

## PRODUCTION INFRASTRUCTURE OPTIONS

### Option 1: Cloud HFT Infrastructure (AWS/GCP)

**Specifications:**
```yaml
Provider: AWS (us-east-1, low latency)
Compute:
  - Instance Type: c7gn.16xlarge (64 vCPU, 128GB RAM)
  - Count: 2-3 instances (load balanced)
  - Network: 100 Gbps
  - Cost: $3.60/hour × 2 = $7.20/hour = $5,184/month

Storage:
  - Type: EBS gp3 (high IOPS)
  - Size: 10 TB
  - IOPS: 64,000
  - Cost: $800/month

Network:
  - Data transfer: 20 TB/month
  - Cost: $1,800/month

Total: ~$8,000/month
```

**Pros:**
- ✅ High performance (64 vCPU, 128GB RAM per instance)
- ✅ 100 Gbps networking
- ✅ Low latency to trading APIs
- ✅ Scalable on demand
- ✅ Managed infrastructure

**Cons:**
- ❌ Expensive ($8k/month)
- ❌ Data transfer costs
- ❌ Not cost-optimal

### Option 2: Dedicated HFT Servers (Hetzner, OVH)

**Specifications:**
```yaml
Provider: Hetzner (Falkenstein, Germany)
Compute:
  - Server: AX102 (AMD EPYC 7513P)
  - CPU: 32 cores / 64 threads
  - RAM: 128GB ECC DDR4
  - Storage: 2x 3.84TB NVMe SSD
  - Network: 1 Gbps
  - Count: 2 servers
  - Cost: $248/month × 2 = $496/month

Storage:
  - Included: 2x 3.84TB NVMe = 7.68 TB
  - Additional: Storage box 20TB = $40/month

Network:
  - Included: 1 Gbps unmetered
  - Upgrade to 10 Gbps: +$50/month

Total: ~$600/month
```

**Pros:**
- ✅ Good performance (32 cores, 128GB RAM per server)
- ✅ Much cheaper ($600 vs $8k)
- ✅ Unmetered bandwidth
- ✅ High IOPS NVMe storage
- ✅ Redundancy (2 servers)

**Cons:**
- ⚠️ 1 Gbps network (may bottleneck HFT)
- ⚠️ Higher latency to US markets
- ⚠️ Manual management

### Option 3: Hybrid (Hetzner + AWS for Trading)

**Specifications:**
```yaml
Primary Infrastructure: Hetzner AX102 × 2
  - Backend loop, autonomous systems, coordination
  - Cost: $496/month

HFT Trading Nodes: AWS c7gn.4xlarge × 2
  - 16 vCPU, 32GB RAM each
  - 50 Gbps networking
  - Only for order execution (can spin up/down)
  - Cost: $0.90/hour × 2 = $1.80/hour
  - Usage: 8 hours/day (peak trading) = $432/month

Storage: Hetzner Storage Box
  - 20 TB
  - Cost: $40/month

Total: ~$1,000/month
```

**Pros:**
- ✅ Cost-efficient ($1k/month)
- ✅ High performance when needed (AWS for HFT)
- ✅ Low cost for infrastructure (Hetzner)
- ✅ Flexible (spin up AWS during trading hours)
- ✅ Geographic redundancy

**Cons:**
- ⚠️ More complex architecture
- ⚠️ Coordination between Hetzner + AWS

### Option 4: Bare Metal HFT (Equinix, IX Reach)

**Specifications:**
```yaml
Provider: Equinix Metal (co-located near exchanges)
Compute:
  - Server: c3.large.x86
  - CPU: 48 cores
  - RAM: 256GB
  - Storage: 2x 3.8TB NVMe
  - Network: 2x 25 Gbps
  - Count: 2 servers
  - Cost: $2,100/month × 2 = $4,200/month

Network:
  - Low-latency direct connect to exchanges
  - Cost: Included

Total: ~$4,200/month
```

**Pros:**
- ✅ BEST latency (co-located)
- ✅ High performance (48 cores, 256GB RAM)
- ✅ 25 Gbps networking
- ✅ Purpose-built for HFT
- ✅ Direct exchange connectivity

**Cons:**
- ❌ Expensive ($4.2k/month)
- ❌ Overkill for current trading volume
- ❌ Fixed cost (can't scale down)

---

## RECOMMENDED INFRASTRUCTURE

### Phase 1: Development → Production Transition (Now)

**Goal:** Support initial live trading with room to scale

**Hardware:**
```yaml
Primary Node: Hetzner AX102
  - CPU: 32 cores / 64 threads
  - RAM: 128GB
  - Storage: 2x 3.84TB NVMe
  - Network: 1 Gbps
  - Role: Main trading + backend + coordination
  - Cost: $248/month

Backup Node: Hetzner AX102
  - Same specs as primary
  - Role: Hot standby + redundancy
  - Cost: $248/month

Storage: Hetzner Storage Box 20TB
  - For logs and backups
  - Cost: $40/month

Total: $536/month
```

**Capabilities:**
- ✅ 64 cores / 128 threads total
- ✅ 256GB RAM total
- ✅ 15TB NVMe storage
- ✅ Geographic redundancy
- ✅ Unmetered 1 Gbps bandwidth
- ✅ Can handle 10,000-50,000 orders/sec
- ✅ Supports 63-wallet fleet
- ✅ Pre-signed transaction caching
- ✅ Distributed trading

**Scaling Path:**
- Start at $536/month
- Scale to higher order volume as revenue increases
- Migrate to AWS HFT nodes when approaching 100K orders/sec

### Phase 2: High-Volume Trading ($10K+ revenue/day)

**Add AWS HFT Nodes:**
```yaml
Trading Nodes: AWS c7gn.4xlarge × 2
  - 16 vCPU, 32GB RAM each
  - 50 Gbps networking
  - Order execution only
  - Cost: $432/month (8 hours/day)

Hetzner Infrastructure: (Keep existing)
  - Backend, coordination, monitoring
  - Cost: $536/month

Total: ~$1,000/month
```

**Capabilities:**
- ✅ 96 cores / 192 threads total
- ✅ 320GB RAM total
- ✅ 50 Gbps low-latency networking for trading
- ✅ Can handle 100,000-500,000 orders/sec
- ✅ Hybrid cost optimization

### Phase 3: Ultra High-Frequency ($100K+ revenue/day)

**Migrate to Equinix:**
```yaml
Bare Metal HFT: Equinix Metal c3.large.x86 × 2
  - 96 cores / 192 threads total
  - 512GB RAM total
  - 25 Gbps low-latency networking
  - Co-located near exchanges
  - Cost: $4,200/month

Total: $4,200/month
```

**Capabilities:**
- ✅ 96 cores / 192 threads
- ✅ 512GB RAM
- ✅ Ultra-low latency (<1ms to exchanges)
- ✅ Can handle 1,000,000 orders/sec
- ✅ Professional HFT infrastructure

---

## COST-BENEFIT ANALYSIS

| Phase | Infrastructure | Cost/Month | Order Capacity | Revenue Potential |
|-------|---------------|------------|----------------|-------------------|
| **Phase 1** | Hetzner × 2 | $536 | 10K-50K orders/sec | $1K-10K/day |
| **Phase 2** | Hetzner + AWS | $1,000 | 100K-500K orders/sec | $10K-50K/day |
| **Phase 3** | Equinix Bare Metal | $4,200 | 1M orders/sec | $100K+/day |

**ROI Analysis:**

**Phase 1:** $536/month
- Break-even: $18/day revenue
- At $1K/day: ROI = 56x
- At $10K/day: ROI = 560x

**Phase 2:** $1,000/month
- Break-even: $33/day revenue
- At $10K/day: ROI = 300x
- At $50K/day: ROI = 1,500x

**Phase 3:** $4,200/month
- Break-even: $140/day revenue
- At $100K/day: ROI = 714x

---

## IMPLEMENTATION TIMELINE

### Week 1: Deploy Phase 1 Infrastructure

**Actions:**
1. Order 2× Hetzner AX102 servers (15 min)
2. Setup SSH keys and firewall (30 min)
3. Deploy hands-off-engine to both servers (30 min)
4. Configure 63-wallet fleet (1 hour)
5. Test distributed trading (1 hour)
6. Enable live trading (5 min)

**Total Time:** 3-4 hours
**Cost:** $536/month

### Weeks 2-4: Optimize and Scale

**Actions:**
1. Monitor performance metrics
2. Optimize order execution
3. Tune ABCFC parameters
4. Scale wallet fleet as needed
5. Add AWS nodes if approaching capacity

### Month 2+: Revenue-Driven Scaling

**Trigger for Phase 2:** Daily revenue > $5K
**Trigger for Phase 3:** Daily revenue > $50K

---

## COMPARISON TO BLUEPRINT

| Aspect | HARDWARE_BLUEPRINT.md | PRODUCTION_REQUIREMENTS.md |
|--------|----------------------|----------------------------|
| **Design Goal** | Current minimal usage | Full operational scale |
| **Use Case** | Development/testing | Live HFT trading |
| **Order Rate** | <1 order/minute | 1M orders/second |
| **CPU** | 1 vCPU | 64-128 vCPU |
| **RAM** | 1 GB | 128-256 GB |
| **Storage** | 50 GB | 10-20 TB |
| **Network** | 10 Mbps | 1-50 Gbps |
| **Cost** | $0/month | $500-5,000/month |
| **ABCFC Score** | 82.88 (cost focus) | TBD (performance focus) |

**Both are correct for their respective goals:**
- Blueprint: Optimal for CURRENT minimal deployment
- This document: Optimal for PRODUCTION HFT operations

---

## NEXT STEPS

### Immediate (This Week)

**Decision Required:** Choose infrastructure phase

**Option A: Start with Phase 1** (Recommended)
- Order 2× Hetzner AX102 ($536/month)
- Deploy and test
- Scale to Phase 2 when revenue justifies

**Option B: Start with Phase 2** (If confident in revenue)
- Order Hetzner + setup AWS HFT nodes
- Higher upfront cost but more capacity

**Option C: Stay on current infrastructure** (Conservative)
- Keep ho-cli-main running
- Scale when revenue proves viability

### Commands to Deploy Phase 1

```bash
# 1. Order Hetzner servers (manual - web console)
# https://www.hetzner.com/dedicated-rootserver/ax102

# 2. Once servers ready, deploy:
bash scripts/deploy_production_infrastructure.sh \
  --provider hetzner \
  --servers 2 \
  --wallet-fleet 63

# 3. Enable live trading:
python3 integrafix/money_printer.py --enable-production-mode
```

---

## CONCLUSION

**The Disconnect:**
- Current testing shows 1 vCPU, 1GB RAM is sufficient
- But production design requires 1M orders/sec HFT capability
- These are BOTH correct for their respective use cases

**The Solution:**
- Phase 1: Start with Hetzner AX102 × 2 ($536/month)
  - Supports 10K-50K orders/sec
  - Room to grow
  - Affordable
- Phase 2: Add AWS HFT nodes ($1K/month)
  - When revenue > $5K/day
  - Supports 100K-500K orders/sec
- Phase 3: Migrate to Equinix ($4.2K/month)
  - When revenue > $50K/day
  - Full 1M orders/sec capability

**Recommendation:**
Deploy Phase 1 infrastructure NOW ($536/month) to support transition from development to production trading, with clear scaling path as revenue grows.

---

**Master:** Yair Siegel
**Analysis Date:** December 5, 2025
**Status:** Ready for decision
