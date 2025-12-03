# ABSOLUTE BOUNDS CONTINUOUS FAN CHART (ABCFC)

## Also known as: Resolution Cone

## KNOWLEDGE BASE FOR: ABCFC Analysis

**File**: `executor/math/resolution_cone.py`
**Purpose**: Novel chart type for binary prediction market visualization
**Created by**: Yair Siegel

---

## NOMENCLATURE

**Absolute Bounds Continuous Fan Chart** breaks down as:
- **Absolute Bounds** = Uses actual min/max outcomes (not percentiles like 5th/95th)
- **Continuous** = Smooth probability gradient (not discrete color bands)
- **Fan Chart** = Uncertainty expands over time (inspired by Bank of England, 1996)

---

## 2D PROBABILITY DENSITY

The ABCFC uses **true 2D probability density** where probability varies in BOTH dimensions:

### X-Axis (Time)
- **Entry (t=0)**: All probability mass at P&L = $0
- **Middle**: Probability spreads as price fluctuates
- **Late (t→resolution)**: Bimodal split toward binary outcomes
- **Resolution**: Two discrete points (best/worst)

### Y-Axis (P&L)
- Gaussian distribution centered on expected value
- Width varies with time (wider mid-way, narrower at endpoints)
- At resolution: collapses to two delta functions

### The Model
```
Price follows bounded random walk with drift toward resolution:

Early (t~0):     Tight Gaussian at entry price
Middle (t~0.5):  Wide Gaussian, peak variance
Late (t~1):      Bimodal Gaussian mixture splitting to 0 and 1
Resolution:      Binary outcome (price = 0 or 1)
```

### Variance Over Time
```
variance(t) = 4 * t * (1-t)   # Peaks at t=0.5, zero at endpoints

     ^
var  │      ╱╲
     │    ╱    ╲
     │  ╱        ╲
     │╱            ╲
     └──────────────→ time
     0    0.5      1
```

This models: uncertainty grows from entry, then collapses at resolution.

---

## WHAT IS A RESOLUTION CONE?

A **Resolution Cone** is a probability visualization designed specifically for binary prediction markets (like Polymarket). It shows how uncertainty expands over time until the market resolves to one of two outcomes.

### Inspired By
- **Bank of England Fan Charts** (1996) - Economic forecasting
- **Cone of Uncertainty** - Hurricane path prediction

### What Makes It Unique
1. **Absolute Bounds** - Uses actual min/max outcomes, not percentiles
2. **Continuous Gradient** - Smooth probability shading, not discrete bands
3. **Binary Outcome Space** - Designed for YES/NO markets (resolves to 0 or 1)
4. **Time-Expanding Cone** - Uncertainty fans out toward resolution date

---

## QUICK START

```python
from executor.math.resolution_cone import plot_resolution_cone, ResolutionCone, analyze_position

# Quick plot
result = plot_resolution_cone(
    entry_price=0.10,        # Bought at 10 cents
    position_size=100,       # $100 position
    prob_yes=0.10,           # 10% probability
    days_to_resolution=30
)
print(f"Chart saved: {result['chart_path']}")

# Just analysis (no chart)
analysis = analyze_position(0.10, 100, prob_yes=0.15)
print(f"Expected: ${analysis['outcomes']['expected']}")

# Full control
cone = ResolutionCone(
    entry_price=0.10,
    position_size=100,
    prob_yes=0.10,
    days=30,
    side="YES"
)
print(f"Best:  +${cone.best_case:.2f}")
print(f"Worst: ${cone.worst_case:.2f}")
```

---

## THE THREE LINES

Every resolution cone has exactly three lines:

### 1. Best Case (Green)
The absolute maximum profit if the market resolves in your favor.

```
For YES position: Best = (1 - entry_price) / entry_price × position_size
For NO position:  Best = entry_price / (1 - entry_price) × position_size

Example: $100 YES @ $0.10
  Shares = $100 / $0.10 = 1000 shares
  Best = 1000 × $1.00 - $100 = +$900
```

### 2. Worst Case (Red)
The absolute maximum loss if the market resolves against you.

```
For both YES and NO: Worst = -position_size (you lose everything)

Example: $100 position
  Worst = -$100
```

### 3. Expected Value (Blue)
The probability-weighted average outcome.

```
Expected = (prob_yes × best_case) + ((1 - prob_yes) × worst_case)

Example: $100 YES @ $0.10, P(YES)=10%
  Expected = 0.10 × $900 + 0.90 × (-$100)
  Expected = $90 - $90 = $0
```

---

## THE GRADIENT

The continuous gradient between best and worst case represents **probability density**:

- **Dark blue** = High probability (near expected value)
- **Light blue** = Low probability (near extremes)
- **White/Clear** = Outside possible range

The gradient uses a Gaussian distribution centered on the expected value, smoothed with a Gaussian filter for continuous shading.

---

## METHODS

### ResolutionCone Class

```python
cone = ResolutionCone(entry_price, position_size, prob_yes, days, side)

# Properties
cone.best_case          # Maximum profit
cone.worst_case         # Maximum loss
cone.expected           # Probability-weighted EV
cone.risk_reward_ratio  # Upside / downside
cone.breakeven_prob     # Probability where EV = 0
cone.edge               # Your prob - market prob

# Methods
cone.plot(save_path, title)           # Generate chart
cone.to_dict()                        # Export as dictionary
cone.get_projection()                 # Get ConeProjection dataclass
cone.get_daily_bounds(day)            # (worst, expected, best) for day
cone.probability_at_outcome(val, day) # Probability density at point
```

### Quick Functions

```python
# Plot and get analysis
result = plot_resolution_cone(entry_price, size, prob_yes, days, side)

# Just analysis
analysis = analyze_position(entry_price, size, prob_yes, side)

# Quick constructor
c = cone(0.10, 100, 0.15, 30, "YES")
```

---

## OUTPUT FORMAT

```python
{
    "type": "resolution_cone",
    "side": "YES",
    "entry_price": 0.10,
    "position_size": 100,
    "prob_yes": 0.10,
    "days": 30,
    "outcomes": {
        "best_case": 900.0,
        "expected": 0.0,
        "worst_case": -100.0
    },
    "metrics": {
        "risk_reward_ratio": 9.0,
        "breakeven_prob": 0.10,
        "edge": 0.0
    }
}
```

---

## KEY INSIGHTS

### Risk/Reward Ratio
```
R:R = |best_case| / |worst_case|

Low probability events have high R:R ratios.
10% event: R:R = 9:1 (risk $100 to win $900)
```

### Breakeven Probability
```
The probability at which EV = 0.

If your estimated probability > breakeven, the bet has +EV.
If your estimated probability < breakeven, the bet has -EV.

For fair pricing: breakeven_prob ≈ entry_price
```

### Edge
```
edge = your_prob - market_prob

Positive edge = you think market underestimates probability
Negative edge = you think market overestimates probability
```

---

## VISUAL INTERPRETATION

```
Profit ($)
    ^
+900|  _____________________________________ Best Case
    |  /
    |  /    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (low probability)
    |  /   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
    |  /  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
    |  / ████████████████████████████████████ (high probability)
   0|--========================================= Expected
    |  \ ████████████████████████████████████
-100|  \___________________________________ Worst Case
    +-------------------------------------------> Days
         0                                   30
```

The "cone" shape shows:
- **Day 0**: No uncertainty (you just entered)
- **Resolution**: Maximum uncertainty range
- **Gradient**: Most likely outcomes are near expected value

---

## INTEGRATION

The Resolution Cone integrates with:
- `executor/polymarket_orders.py` - `plot_profit_projection()` method
- `executor/yair_auto_trader.py` - Position analysis
- Trading decisions - Kelly sizing with visual confirmation

---

## SUMMARY

**Resolution Cone** = Fan Chart + Binary Outcomes + Continuous Gradient

A unique visualization for prediction markets that shows the expanding range of possible outcomes while highlighting probability density through smooth shading.
