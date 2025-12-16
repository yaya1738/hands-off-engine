# Cloud Billing Model Breakdown

## Billing Models by Provider

---

## Recommended Architecture Billing:

### Node 1: Hetzner US (Dedicated Server AX41)
**Billing:** Monthly commitment
- **Cost:** $49.90/month fixed
- **Can't pause:** Billed monthly regardless of usage
- **Minimum term:** Usually 1 month, can cancel anytime
- **Billed:** Monthly in advance

### Node 2: Hetzner EU (Dedicated Server AX41)
**Billing:** Monthly commitment
- **Cost:** $49.90/month fixed
- **Same as Node 1**

### Node 3: Oracle Cloud Free (ARM A1)
**Billing:** FREE FOREVER
- **Cost:** $0.00 (no billing at all)
- **No credit card charges**
- **Always Free tier**

### Node 4: Vast.ai GPU (RTX 4090)
**Billing:** PER-SECOND (most flexible!)
- **Cost:** ~$0.80/hour WHEN RUNNING
- **Can pause:** Only pay when instance is running
- **Stop it:** $0 cost when stopped
- **Monthly:** $584 IF running 24/7
- **Billed:** Pay-as-you-go, charged to balance

---

## Billing Comparison:

| Provider | Model | Flexibility | Cost Control |
|----------|-------|-------------|--------------|
| **Hetzner Dedicated** | Monthly | ❌ Can't pause | Fixed cost |
| **Hetzner Cloud** | Hourly* | ⚠️ Billed while exists | Can delete |
| **Oracle Free** | FREE | ✅ Free forever | No cost |
| **Vast.ai GPU** | Per-second | ✅ Pause anytime | Full control |
| **AWS** | Per-second | ✅ Very flexible | Pay what you use |
| **DigitalOcean** | Hourly | ⚠️ Billed while exists | Capped at monthly |

*Hourly billing usually means charged for each hour the server EXISTS (not running time)

---

## Cost Optimization Strategies:

### Strategy 1: Always-On (Full Monthly Cost)
```
Node 1: Hetzner        $49.90/mo  (always billed)
Node 2: Hetzner        $49.90/mo  (always billed)
Node 3: Oracle Free    $0.00/mo   (free)
Node 4: GPU 24/7       $584.00/mo (730 hours)
                       ──────────
Total:                 $683.80/month
```

### Strategy 2: GPU On-Demand (Optimized)
```
Node 1: Hetzner        $49.90/mo  (always billed)
Node 2: Hetzner        $49.90/mo  (always billed)
Node 3: Oracle Free    $0.00/mo   (free)
Node 4: GPU 8hr/day    $195.00/mo (240 hours @ $0.80/hr)
                       ──────────
Total:                 $294.80/month
```
**Savings:** $389/month (57% cheaper!)

### Strategy 3: Minimal (Development)
```
Node 1: Hetzner        $49.90/mo  (always billed)
Node 3: Oracle Free    $0.00/mo   (free)
Node 4: GPU as needed  ~$50/mo    (occasional use)
                       ──────────
Total:                 ~$100/month
```

---

## GPU Billing Deep Dive:

### Vast.ai (Per-Second Billing)
```
Running:     $0.80/hour
Stopped:     $0.00/hour
Paused:      $0.00/hour

Examples:
- 8 hours/day:  8 × 30 × $0.80 = $192/month
- 12 hours/day: 12 × 30 × $0.80 = $288/month
- 24 hours/day: 24 × 30 × $0.80 = $576/month
- Weekend only: 8 × 8 × $0.80 = $51/month
```

**You only pay when GPU is RUNNING.**

### RunPod (Similar)
```
Per-minute billing
Can pause/stop anytime
Only charged for running time
Slightly different pricing (~$0.70-0.90/hr for 4090)
```

---

## Hetzner Billing Details:

### Dedicated Servers (AX41, AX41-NVMe)
- **Billed:** Monthly in advance
- **Minimum:** 1 month
- **Cancellation:** End of month
- **Can't pause:** Always billed
- **Setup:** Usually instant (sometimes 24h wait)

**Example:**
- Order on Dec 4: Billed $49.90 immediately
- Runs: Dec 4 - Jan 4
- Cancel Dec 20: Still billed for full December, ends Jan 4
- Charged again: Jan 4 for next month

### Cloud Servers (CPX, CCX)
- **Billed:** Hourly
- **Charged:** While server exists (not just running)
- **Can delete:** Stop paying once deleted
- **Minimum:** No minimum

**Example:**
- Create Dec 4 at 10am
- Delete Dec 10 at 2pm
- Billed: 6 days, 4 hours = 148 hours × $0.087 = $12.88

---

## Oracle Cloud Free Tier:

**Always Free Resources:**
```
ARM Ampere A1:
- 4 OCPU (cores)
- 24GB RAM
- 200GB storage
- FOREVER FREE (no expiration)

x86 Micro:
- 1 OCPU
- 1GB RAM
- 50GB storage
- FOREVER FREE

Cost: $0
Billing: None
Expiration: Never
Catches: None (really free)
```

---

## Recommended Billing Strategy:

### For Hands-Off System:

**BASE COMPUTE: Monthly (Hetzner)**
- Nodes 1-2 run 24/7 (core infrastructure)
- Monthly billing = predictable cost
- Can't optimize these (always needed)
- **Cost:** $99.80/month fixed

**GPU: On-Demand (Vast.ai)**
- Only run when doing ML/AI work
- Start when needed, stop when done
- Massive cost savings
- **Cost:** $0-$584/month (you control it)

**FREE TIER: Always (Oracle)**
- No cost, no optimization needed
- **Cost:** $0 forever

---

## Your Actual Monthly Bill:

### Minimal Usage (Development):
```
Hetzner (2 nodes):     $99.80
Oracle Free:           $0.00
GPU (occasional):      ~$30.00
                       ───────
Total:                 ~$130/month
```

### Normal Usage:
```
Hetzner (2 nodes):     $99.80
Oracle Free:           $0.00
GPU (8hr/day):         $192.00
                       ───────
Total:                 ~$292/month
```

### Heavy Usage (24/7 GPU):
```
Hetzner (2 nodes):     $99.80
Oracle Free:           $0.00
GPU (24/7):            $584.00
                       ───────
Total:                 $683.80/month
```

---

## Key Takeaway:

✅ **Hetzner:** Monthly billing (fixed cost, can't optimize)
✅ **Oracle:** FREE (no billing)
✅ **GPU:** Per-second (HUGE cost control - only pay when running)

**You control your bill by:**
1. Fixed base: $99.80/month (can't change)
2. GPU usage: $0-584/month (you decide)
3. Total range: $100-$684/month

**Most realistic:** ~$300/month with smart GPU usage

---

Master: Yair Siegel
Date: 2025-12-04
