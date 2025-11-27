# Cash Explosion Opportunity Examples

Quick reference for adding high-impact cash opportunities to the system.

---

## Quick Add Examples

### Trading Opportunity
```bash
python3 business/quick_add_opportunity.py \
  "BTC prediction market arbitrage" \
  500 \
  --hours 12 \
  --effort 2 \
  --confidence 0.8 \
  --priority critical \
  --category trading
```

### Gig Work
```bash
python3 business/quick_add_opportunity.py \
  "Upwork React development contract" \
  1200 \
  --hours 72 \
  --effort 8 \
  --confidence 0.7 \
  --priority high \
  --category contract
```

### Quick Sale
```bash
python3 business/quick_add_opportunity.py \
  "Sell unused MacBook Pro" \
  800 \
  --hours 48 \
  --effort 2 \
  --confidence 0.9 \
  --priority high \
  --category sale
```

### Consulting Gig
```bash
python3 business/quick_add_opportunity.py \
  "AI automation consulting session" \
  300 \
  --hours 24 \
  --effort 3 \
  --confidence 0.8 \
  --priority high \
  --category gig
```

---

## Category Guidelines

### Trading
- Polymarket opportunities
- Arbitrage opportunities
- Market inefficiencies
- **Risk:** Medium-High
- **Time to Cash:** Fast (hours to days)

### Gig
- One-off tasks
- TaskRabbit, Fiverr, etc.
- Quick technical help
- **Risk:** Low
- **Time to Cash:** Fast (same day to 1 week)

### Contract
- Freelance projects
- Upwork, contract work
- Technical consulting
- **Risk:** Low-Medium
- **Time to Cash:** Medium (1-4 weeks)

### Sale
- Selling items
- Liquidating assets
- Physical goods
- **Risk:** Low
- **Time to Cash:** Fast-Medium (1-7 days)

### Investment
- Deployment of capital for returns
- Usually requires capital
- **Risk:** Varies
- **Time to Cash:** Slow (weeks to months)

---

## Priority Levels

### CRITICAL
- Needed for emergency cash < 48 hours
- High confidence (>70%)
- Fast execution
- **Examples:** Immediate gig work, quick sales

### HIGH
- Significant revenue opportunity
- Good confidence (>60%)
- Fast to medium execution
- **Examples:** Trading opportunities, contracts

### MEDIUM
- Standard opportunities
- Moderate confidence
- Medium execution time
- **Examples:** Most freelance work

### LOW
- Long-term opportunities
- Lower confidence or slower execution
- **Examples:** Investment opportunities, long contracts

---

## Emergency Cash Criteria

Opportunities that qualify for EMERGENCY fast cash:

✅ **Time to Cash:** < 48 hours
✅ **Confidence:** > 60%
✅ **Expected Revenue:** > $100
✅ **Low/No Capital Required**

These will be prioritized in emergency mode.

---

## Template: Full Add

For more complex opportunities, use interactive mode:

```bash
python3 business/cash_explosion_opportunities.py --add
```

Or create JSON:

```json
{
  "title": "Opportunity Title",
  "description": "Detailed description",
  "category": "trading|gig|contract|sale|investment|other",
  "potential_revenue": 1000.0,
  "time_to_cash_hours": 24,
  "effort_hours": 4,
  "required_capital": 0,
  "confidence": 0.7,
  "risk_level": "low|medium|high",
  "priority": "critical|high|medium|low",
  "action_steps": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "notes": "Additional notes"
}
```

---

## Today's Opportunity Template

When you discover an opportunity TODAY, add it immediately:

```bash
# Method 1: Quick add (fastest)
python3 business/quick_add_opportunity.py "Opportunity Name" REVENUE

# Method 2: Interactive (more detail)
./business/add_todays_opportunity.sh

# Method 3: Full control
python3 business/cash_explosion_opportunities.py --add
```

Then view:
```bash
python3 business/cash_explosion_opportunities.py --dashboard
```

---

## Tracking Execution

Once added, opportunities can be:

1. **Identified** → just discovered
2. **In Progress** → actively working on it
3. **Completed** → cash received
4. **Failed** → didn't work out

Update status via execution log or scripts (coming soon).

---

## Integration with Emergency System

The cash explosion system is integrated with emergency response:

- Emergency opportunities (< 48hr cash) are flagged
- Dashboard shows current financial context
- Opportunities are prioritized by urgency score
- Expected value helps emergency planning

**View both together:**
```bash
# Emergency status
python3 business/emergency_status_monitor.py

# Cash opportunities
python3 business/cash_explosion_opportunities.py --dashboard
```

---

## Example: Adding Today's Opportunity

Let's say you found a Polymarket arbitrage opportunity:

```bash
python3 business/quick_add_opportunity.py \
  "Polymarket BTC-100k arbitrage" \
  350 \
  --hours 6 \
  --effort 1 \
  --confidence 0.85 \
  --priority critical \
  --category trading
```

Output:
```
✅ Added: Polymarket BTC-100k arbitrage
   Expected: $297.50
   Hourly Rate: $297.50/hr
   ID: OPP-20251127140730
```

Then execute:
```bash
# View in dashboard
python3 business/cash_explosion_opportunities.py

# See how it impacts emergency plan
python3 business/emergency_financial_response.py
```

---

**Remember:** In emergency mode, prioritize opportunities with:
- Fastest time to cash
- Highest confidence
- Best hourly rate
- Lowest risk

The system automatically scores and ranks these for you!
