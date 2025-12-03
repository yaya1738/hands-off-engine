# Money & Finance - Advanced Technical Knowledge

## Deep internals and mathematics of monetary systems.

---

# SECTION 1: MONETARY THEORY DEEP DIVE

## 1.1 Quantity Theory of Money

### Fisher Equation
```
M × V = P × Y

Where:
- M = Money supply
- V = Velocity of money
- P = Price level
- Y = Real output

In growth rates:
ΔM/M + ΔV/V = ΔP/P + ΔY/Y
```

### Cambridge Equation
```
M = k × P × Y

Where:
- k = Fraction of income held as money (1/V)
- Represents money demand perspective
```

### Money Demand Functions

**Keynesian Liquidity Preference:**
```
M/P = L(Y, i)

Where:
- L₁(Y) = Transaction demand (positive)
- L₂(i) = Speculative demand (negative)

M/P = L₁(Y) + L₂(i)
```

**Baumol-Tobin Model:**
```
Optimal cash holding:
M* = √(2 × T × F / i)

Where:
- T = Total transactions
- F = Fixed cost per withdrawal
- i = Interest rate

Average cash balance = M*/2
```

### Friedman's Modern Quantity Theory
```
Md/P = f(Yp, rb - rm, re - rm, πe - rm)

Where:
- Yp = Permanent income
- rb = Bond return
- re = Equity return
- rm = Money return
- πe = Expected inflation
```

## 1.2 Money Creation Mechanics

### Bank Balance Sheet
```
ASSETS                  LIABILITIES
────────────────────────────────────
Reserves      $100     Deposits    $900
Loans         $800     Equity      $100
Securities    $100
────────────────────────────────────
Total        $1,000    Total     $1,000
```

### Deposit Multiplication Process
```
Initial deposit: D₀
Reserve requirement: r
Money multiplier: m = 1/r

Round 1: Bank A receives D₀
         Reserves: r × D₀
         Loans: (1-r) × D₀

Round 2: Bank B receives (1-r) × D₀
         Reserves: r × (1-r) × D₀
         Loans: (1-r)² × D₀

Total deposits = D₀ × [1 + (1-r) + (1-r)² + ...]
               = D₀ × (1/r)
               = D₀ × m
```

### Extended Money Multiplier
```
m = (1 + c) / (r + e + c)

Where:
- c = Currency-deposit ratio
- r = Required reserve ratio
- e = Excess reserve ratio

Example:
c = 0.40, r = 0.10, e = 0.05
m = 1.40 / 0.55 = 2.55
```

### Endogenous Money Theory
```
Loans create deposits:
1. Bank makes loan → Credit account
2. New deposit created simultaneously
3. Bank seeks reserves after

Money supply is demand-driven:
Ms = f(Md, CB accommodation)
```

## 1.3 Velocity of Money

### Income Velocity
```
V = (P × Y) / M = Nominal GDP / Money Supply

V₁ = GDP / M1 (narrow)
V₂ = GDP / M2 (broad)
```

### Velocity Determinants
```
V = f(i, financial innovation, payment technology,
      income distribution, expectations)

Higher interest rates → Higher V (opportunity cost)
Better payment tech → Higher V (faster turnover)
Uncertainty → Lower V (precautionary holdings)
```

### Velocity Stability
```
Short-run: V volatile (speculative demand shifts)
Long-run: V more stable (institutional factors)

Post-2008: V collapsed due to:
- Quantitative easing
- Increased money demand
- Liquidity trap conditions
```

---

# SECTION 2: CENTRAL BANK OPERATIONS

## 2.1 Open Market Operations

### Repo Operations
```
REPO (Repurchase Agreement):
Day 0: Fed buys securities, injects reserves
Day T: Fed sells back, drains reserves

Reverse Repo:
Day 0: Fed sells securities, drains reserves
Day T: Fed buys back, injects reserves

Repo rate = (Repurchase price - Purchase price) / Purchase price × (360/T)
```

### Permanent vs Temporary OMO
```
Permanent:
- Outright purchases/sales
- Permanent change in money base
- Used for long-term policy

Temporary:
- Repo/reverse repo
- Short-term liquidity management
- Daily fine-tuning
```

### Reserve Management
```
Reserve demand: Rd = f(deposits, reserve req, payment needs)
Reserve supply: Rs = Non-borrowed + Borrowed reserves

Fed funds rate determined by:
FFR = f(Rs - Rd, IOER, RRP rate)

Corridor system:
- Ceiling: Discount rate
- Floor: IOER (Interest on Excess Reserves)
```

## 2.2 Discount Window

### Lending Facilities
```
Primary Credit:
- For sound institutions
- Rate = Target FFR + 50bp
- No questions asked

Secondary Credit:
- For troubled institutions
- Rate = Primary + 50bp
- More scrutiny

Seasonal Credit:
- For small banks with seasonal patterns
- Rate = Average of FFR and CD rates
```

### Lender of Last Resort
```
Bagehot's Principles:
1. Lend freely
2. At penalty rate
3. Against good collateral
4. To solvent but illiquid institutions

Modern application:
- Emergency lending authority (13.3)
- Collateral requirements
- Systemic importance consideration
```

## 2.3 Reserve Requirements

### Required Reserves Calculation
```
Required reserves = Σ(ri × Di)

Where:
- ri = Reserve ratio for deposit type i
- Di = Amount of deposits type i

Example (US pre-2020):
- 0% on first $16.9M
- 3% on $16.9M to $127.5M
- 10% on over $127.5M
```

### Reserve Averaging
```
Average reserves over maintenance period:
R̄ = (1/n) × Σ Rt

Carry-over provisions:
- Excess can offset deficiency
- Up to 4% of requirement
- 2-period carry-over
```

## 2.4 Quantitative Easing Mechanics

### Large-Scale Asset Purchases
```
Fed buys assets → Creates reserves
Bank receives reserves → Deposits increase
Portfolio balance channel:
- Lower long-term yields
- Wealth effect
- Exchange rate effect

QE transmission:
1. Direct purchase → Seller gets cash
2. Seller rebalances → Buys other assets
3. Asset prices rise → Yields fall
4. Lower borrowing costs → Stimulus
```

### Balance Sheet Mechanics
```
Fed Balance Sheet:

ASSETS                    LIABILITIES
─────────────────────────────────────────
Treasury Securities      Currency in circ.
MBS                      Bank reserves
Loans to banks           Reverse repo
Foreign exchange         Treasury deposits
Gold                     Fed capital
─────────────────────────────────────────

QE: Asset side expands, liability (reserves) expands
QT: Asset side contracts, reserves contract
```

### Yield Curve Control
```
Target: Specific yield on specific maturity
Mechanism: Unlimited purchase commitment

Example (Japan):
- 10-year JGB target: ~0%
- BoJ buys whatever needed to maintain

Credibility effect:
- Market expects intervention
- Yields stay near target
- Minimal actual purchases needed
```

---

# SECTION 3: INTEREST RATE MODELS

## 3.1 Term Structure Models

### Expectations Hypothesis
```
(1 + in)^n = (1 + i1)(1 + E[i1,2])(1 + E[i2,3])...(1 + E[in-1,n])

Forward rate = Expected future spot rate + Risk premium

fn,n+1 = E[in,n+1] + term premium
```

### Vasicek Model
```
dr = a(b - r)dt + σdW

Where:
- a = Speed of mean reversion
- b = Long-run mean rate
- σ = Volatility
- dW = Wiener process

Bond price:
P(t,T) = A(t,T) × e^(-B(t,T)×r(t))

Where:
B(t,T) = (1 - e^(-a(T-t))) / a
A(t,T) = exp[(B-T+t)(a²b - σ²/2)/a² - σ²B²/4a]
```

### Cox-Ingersoll-Ross (CIR) Model
```
dr = a(b - r)dt + σ√r dW

Properties:
- Rate stays positive (if 2ab ≥ σ²)
- Mean reverting
- Volatility proportional to √r

Bond price similar form with different A, B
```

### Nelson-Siegel Model
```
y(τ) = β₀ + β₁[(1 - e^(-τ/λ)) / (τ/λ)] +
       β₂[(1 - e^(-τ/λ)) / (τ/λ) - e^(-τ/λ)]

Where:
- β₀ = Long-term level (level)
- β₁ = Short-term component (slope)
- β₂ = Medium-term component (curvature)
- λ = Decay parameter
```

### Svensson Extension
```
y(τ) = β₀ + β₁[(1-e^(-τ/λ₁))/(τ/λ₁)] +
       β₂[(1-e^(-τ/λ₁))/(τ/λ₁) - e^(-τ/λ₁)] +
       β₃[(1-e^(-τ/λ₂))/(τ/λ₂) - e^(-τ/λ₂)]

Additional hump for better fit
```

## 3.2 Forward Rate Analysis

### Forward Rate Calculation
```
Discrete:
f(t₁, t₂) = [(1 + s₂)^t₂ / (1 + s₁)^t₁]^(1/(t₂-t₁)) - 1

Continuous:
f(t₁, t₂) = (s₂ × t₂ - s₁ × t₁) / (t₂ - t₁)

Instantaneous forward:
f(t) = s(t) + t × ds/dt
```

### Forward Rate Agreement (FRA)
```
FRA payoff at settlement:
Payoff = Notional × (R - K) × τ / (1 + R × τ)

Where:
- R = Reference rate at fixing
- K = FRA rate
- τ = Day count fraction

FRA valuation:
V = Notional × (F - K) × τ × DF

Where F = Forward rate, DF = Discount factor
```

## 3.3 Real Interest Rates

### Fisher Equation
```
(1 + i) = (1 + r) × (1 + πe)

Approximation:
i ≈ r + πe

Where:
- i = Nominal rate
- r = Real rate
- πe = Expected inflation
```

### TIPS-Based Real Rates
```
Real yield from TIPS:
r = y(TIPS) - Liquidity premium

Break-even inflation:
BEI = y(Nominal) - y(TIPS)
    = πe + Inflation risk premium - TIPS liquidity premium
```

### Natural Rate of Interest (r*)
```
Wicksellian natural rate:
r* = Rate that equilibrates saving and investment

Laubach-Williams model:
r* = g + demographic factors + other

Estimation challenges:
- Not directly observable
- Model dependent
- Varies over time
```

---

# SECTION 4: YIELD CURVE ANALYSIS

## 4.1 Yield Curve Construction

### Bootstrapping Spot Rates
```
From par yields to spot rates:

Year 1: s₁ = y₁ (par yield)

Year 2:
100 = C/(1+s₁) + (100+C)/(1+s₂)²
Solve for s₂

Year n:
100 = Σ[C/(1+sₜ)^t] + (100+C)/(1+sₙ)^n
Solve for sₙ sequentially
```

### Spline Interpolation
```
Cubic spline between knot points:
S(t) = aᵢ + bᵢ(t-tᵢ) + cᵢ(t-tᵢ)² + dᵢ(t-tᵢ)³

Constraints:
- Continuity: S(tᵢ⁻) = S(tᵢ⁺)
- Smooth first derivative
- Smooth second derivative
- Natural spline: S''(t₀) = S''(tₙ) = 0
```

### Curve Fitting
```
Objective: Minimize pricing error

min Σ wᵢ × (Pᵢ^model - Pᵢ^market)²

Subject to: Smoothness constraints

Methods:
- Least squares
- Maximum smoothness
- Regularized fitting
```

## 4.2 Yield Curve Shapes

### Normal Curve
```
Shape: Upward sloping
Interpretation:
- Expected rate increases
- Positive term premium
- Economic expansion expected
```

### Inverted Curve
```
Shape: Downward sloping
Interpretation:
- Expected rate cuts
- Recession predictor
- Flight to safety

Predictive power:
- 10Y-2Y spread inversion
- 12-24 months before recession
- ~80% accuracy historically
```

### Flat Curve
```
Shape: Little slope
Interpretation:
- Transition phase
- Uncertainty
- Monetary policy pivot expected
```

### Humped Curve
```
Shape: Rises then falls
Interpretation:
- Near-term rate hikes expected
- Long-term rates anchored
- Credible inflation target
```

## 4.3 Duration and Convexity

### Macaulay Duration
```
D = Σ[t × wₜ]

Where:
wₜ = PV(CFₜ) / P = CFₜ/(1+y)^t / P

Example:
5-year bond, 5% coupon, 5% yield:
D = (1×5/1.05 + 2×5/1.05² + ... + 5×105/1.05⁵) / 100
D ≈ 4.55 years
```

### Modified Duration
```
D* = D / (1 + y/m)

Where m = compounding frequency

Price sensitivity:
ΔP/P ≈ -D* × Δy

Example:
D* = 4.33, Δy = 0.01 (100bp)
ΔP/P ≈ -4.33%
```

### Convexity
```
C = (1/P) × Σ[t(t+1) × PV(CFₜ)] / (1+y)²

Price change with convexity:
ΔP/P ≈ -D* × Δy + (1/2) × C × (Δy)²

Convexity benefit:
- Price rises more when yields fall
- Price falls less when yields rise
```

### Key Rate Duration
```
Sensitivity to specific point on curve:
KRDᵢ = -∂P/∂yᵢ × (1/P)

Sum of KRDs = Effective duration
Allows targeted hedging
```

---

# SECTION 5: FOREIGN EXCHANGE MATHEMATICS

## 5.1 Exchange Rate Determination

### Purchasing Power Parity (PPP)
```
Absolute PPP:
S = Pd / Pf

Where:
- S = Spot rate (domestic per foreign)
- Pd = Domestic price level
- Pf = Foreign price level

Relative PPP:
ΔS/S = πd - πf

Expected depreciation = Inflation differential
```

### Interest Rate Parity

**Covered Interest Rate Parity (CIP):**
```
F/S = (1 + id) / (1 + if)

Where:
- F = Forward rate
- S = Spot rate
- id = Domestic interest rate
- if = Foreign interest rate

No arbitrage condition:
(1 + id) = (S/F) × (1 + if)
```

**Uncovered Interest Rate Parity (UIP):**
```
E[S₁]/S₀ = (1 + id) / (1 + if)

Expected depreciation = Interest differential
Requires risk neutrality
Empirically: Forward premium puzzle
```

### Monetary Model
```
s = (m - m*) - φ(y - y*) + λ(i - i*)

Where:
- s = Log exchange rate
- m = Log money supply
- y = Log output
- i = Interest rate
- * = Foreign country

Long-run: Money supply drives exchange rate
```

### Portfolio Balance Model
```
Includes wealth effects and risk:

W = M + B + SF*

Where:
- W = Wealth
- M = Money
- B = Domestic bonds
- SF* = Foreign bonds in domestic currency

Exchange rate determined by portfolio allocation
```

## 5.2 FX Forwards and Swaps

### Forward Points
```
Forward points = F - S

Forward premium/discount:
FP = (F - S) / S × (360/days) × 100

Expressed in pips (0.0001 for most pairs)
```

### FX Swap Valuation
```
FX Swap = Spot + Forward (opposite directions)

Near leg: Exchange currencies at spot
Far leg: Exchange back at forward

Swap points = Interest rate differential effect
```

### Cross Rates
```
Direct calculation:
EUR/GBP = EUR/USD × USD/GBP = EUR/USD / GBP/USD

Triangular arbitrage:
If EUR/USD × USD/GBP × GBP/EUR ≠ 1
→ Arbitrage opportunity exists
```

## 5.3 Currency Options

### Garman-Kohlhagen Model
```
Call: C = Se^(-rf×T) × N(d₁) - Ke^(-rd×T) × N(d₂)
Put:  P = Ke^(-rd×T) × N(-d₂) - Se^(-rf×T) × N(-d₁)

Where:
d₁ = [ln(S/K) + (rd - rf + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T

- rd = Domestic rate
- rf = Foreign rate
- σ = FX volatility
```

### Risk Reversals
```
Risk reversal = Call IV - Put IV
(Same delta, opposite direction)

Positive RR: Market expects appreciation
Negative RR: Market expects depreciation

Measures market skew/sentiment
```

### Volatility Smile
```
FX options typically show smile:
- ATM: Lowest IV
- OTM calls/puts: Higher IV

Reflects:
- Jump risk
- Fat tails in FX returns
- Central bank intervention risk
```

---

# SECTION 6: INFLATION DYNAMICS

## 6.1 Phillips Curve

### Original Phillips Curve
```
πt = α - β × ut

Wage inflation inversely related to unemployment
```

### Expectations-Augmented (Friedman-Phelps)
```
πt = πe + α - β × (ut - u*)

Where:
- πe = Expected inflation
- u* = Natural rate of unemployment

Long-run: No trade-off (vertical at u*)
Short-run: Trade-off exists
```

### New Keynesian Phillips Curve
```
πt = β × E[πt+1] + κ × xt

Where:
- β = Discount factor
- κ = Slope (output gap sensitivity)
- xt = Output gap

Purely forward-looking
Inflation depends on expected future inflation
```

### Hybrid Phillips Curve
```
πt = γf × E[πt+1] + γb × πt-1 + κ × xt

Where:
- γf = Forward-looking weight
- γb = Backward-looking weight (inertia)
- γf + γb = 1

Better empirical fit
```

## 6.2 Inflation Expectations

### Survey-Based Measures
```
Household surveys:
- Michigan Survey
- EU Consumer Surveys

Professional forecasts:
- Survey of Professional Forecasters
- Consensus Economics

Central tendency and dispersion matter
```

### Market-Based Measures
```
Break-even inflation:
BEI = Nominal yield - TIPS yield

Inflation swaps:
Fixed rate that equals expected CPI

Adjustments needed:
- Liquidity premium
- Inflation risk premium
- Convexity adjustment
```

### Anchoring of Expectations
```
Well-anchored:
- Long-term expectations stable at target
- Not sensitive to actual inflation

De-anchored:
- Long-term expectations drift
- Respond to actual inflation
- Policy credibility concern

Test: Correlation of long-term expectations with recent inflation
```

## 6.3 Central Bank Reaction Functions

### Taylor Rule
```
it = r* + πt + 0.5(πt - π*) + 0.5(yt - y*)

Where:
- it = Target interest rate
- r* = Real neutral rate
- πt = Inflation
- π* = Target inflation (2%)
- yt - y* = Output gap

Prescriptive vs Descriptive
```

### Variations
```
Forward-looking Taylor rule:
it = r* + E[πt+1] + 0.5(E[πt+1] - π*) + 0.5E[yt+1]

Interest rate smoothing:
it = ρ × it-1 + (1-ρ) × it^Taylor

Asymmetric response:
Different coefficients for positive/negative gaps
```

### Optimal Monetary Policy
```
Loss function:
L = E[Σβ^t × (πt² + λxt²)]

Minimize loss subject to Phillips Curve constraint

Results in:
- Flexible inflation targeting
- Gradual adjustment to shocks
- History dependence
```

---

# SECTION 7: BANKING & CREDIT ANALYSIS

## 7.1 Bank Capital Adequacy

### Basel III Capital Ratios
```
CET1 Ratio = Common Equity Tier 1 / RWA ≥ 4.5%
Tier 1 Ratio = Tier 1 Capital / RWA ≥ 6%
Total Capital = (Tier 1 + Tier 2) / RWA ≥ 8%

Plus buffers:
- Conservation buffer: 2.5%
- Countercyclical buffer: 0-2.5%
- G-SIB surcharge: 1-3.5%
```

### Risk-Weighted Assets
```
RWA = Σ(Exposure × Risk Weight)

Standardized approach weights:
- Cash, sovereigns (0 risk): 0%
- Banks: 20-150%
- Corporates: 20-150%
- Retail: 75%
- Residential mortgages: 35%
- Commercial RE: 100%
```

### Internal Ratings-Based (IRB)
```
RWA = K × EAD × 12.5

Where:
K = LGD × N[(1-R)^(-0.5) × G(PD) + (R/(1-R))^0.5 × G(0.999)]
    - PD × LGD

- PD = Probability of default
- LGD = Loss given default
- EAD = Exposure at default
- R = Correlation
- N = Standard normal CDF
- G = Inverse standard normal
```

## 7.2 Credit Risk Modeling

### Merton Model
```
Equity as call option on firm assets:
E = V × N(d₁) - D × e^(-rT) × N(d₂)

Where:
d₁ = [ln(V/D) + (r + σv²/2)T] / (σv√T)
d₂ = d₁ - σv√T

- V = Firm value
- D = Debt face value
- σv = Asset volatility

Probability of default:
PD = N(-d₂)
```

### Credit Spreads
```
Credit spread = Yield on risky bond - Risk-free yield

Components:
- Expected loss = PD × LGD
- Risk premium = Compensation for uncertainty
- Liquidity premium
- Tax effects

Spread ≈ PD × LGD × (1 + Risk premium factor)
```

### Credit Value Adjustment (CVA)
```
CVA = LGD × Σ EE(tᵢ) × DF(tᵢ) × [PD(tᵢ) - PD(tᵢ₋₁)]

Where:
- EE(t) = Expected exposure at time t
- DF(t) = Discount factor
- PD(t) = Cumulative default probability

Bilateral CVA includes DVA (own default risk)
```

## 7.3 Liquidity Risk

### Liquidity Coverage Ratio (LCR)
```
LCR = HQLA / Net cash outflows (30 days) ≥ 100%

HQLA categories:
- Level 1: Cash, central bank reserves, govt bonds (100%)
- Level 2A: Other govt, covered bonds (85%)
- Level 2B: Corporate bonds, equities (50-75%)
```

### Net Stable Funding Ratio (NSFR)
```
NSFR = Available stable funding / Required stable funding ≥ 100%

ASF categories (by stability):
- Tier 1 capital: 100%
- Stable deposits: 95%
- Less stable deposits: 90%
- Wholesale funding <1yr: 50%
- Wholesale funding <6mo: 0%
```

### Liquidity Risk Metrics
```
Bid-ask spread: Transaction cost measure
Market depth: Volume to move price
Resilience: Speed of price recovery

Liquidity-adjusted VaR:
LVaR = VaR + Liquidation cost
     = VaR + (Position × Spread / 2)
```

---

# SECTION 8: DERIVATIVES PRICING

## 8.1 Option Greeks Deep Dive

### Delta
```
δ = ∂V/∂S

Call delta: N(d₁) ∈ [0, 1]
Put delta: N(d₁) - 1 ∈ [-1, 0]

Delta hedging:
Hold Δ shares per option written
Rebalance as delta changes
```

### Gamma
```
Γ = ∂²V/∂S² = ∂Δ/∂S

Γ = N'(d₁) / (S × σ × √T)

Maximum at ATM
Increases as expiry approaches (for ATM)

Gamma risk:
- Long gamma: Profit from volatility
- Short gamma: Loss from large moves
```

### Theta
```
Θ = ∂V/∂t

Call: Θ = -[S×N'(d₁)×σ/(2√T)] - r×K×e^(-rT)×N(d₂)
Put:  Θ = -[S×N'(d₁)×σ/(2√T)] + r×K×e^(-rT)×N(-d₂)

Time decay: Options lose value over time
Theta-gamma relationship: Θ + ½σ²S²Γ + rSΔ = rV
```

### Vega
```
ν = ∂V/∂σ

ν = S × √T × N'(d₁)

Same for calls and puts (put-call parity)
Maximum at ATM
Increases with time to expiry

Vega hedging: Use options of different strikes/expiries
```

### Rho
```
ρ = ∂V/∂r

Call: ρ = K × T × e^(-rT) × N(d₂)
Put:  ρ = -K × T × e^(-rT) × N(-d₂)

Smaller for short-dated options
```

## 8.2 Exotic Options

### Barrier Options
```
Knock-out: Cease to exist if barrier hit
Knock-in: Come into existence if barrier hit

Down-and-out call (S₀ > H):
C_do = C_vanilla - C_di

Rebate possible at barrier hit

Pricing: Reflection principle, PDE methods
```

### Asian Options
```
Payoff based on average price:
- Arithmetic average: No closed form
- Geometric average: Closed form exists

Arithmetic Asian call (approximate):
Similar to Black-Scholes with adjusted volatility
σ_adj ≈ σ / √3 (continuous averaging)
```

### Lookback Options
```
Floating strike lookback call:
Payoff = S_T - min(S_t)

Fixed strike lookback call:
Payoff = max(max(S_t) - K, 0)

Closed form solutions exist
```

### Compound Options
```
Option on an option

Call on call: Right to buy a call at price K₁ at T₁
Total exercise: First at T₁, underlying at T₂

Two critical values:
- S* where call value = K₁ at T₁
- Exercise if S > S*
```

## 8.3 Interest Rate Derivatives

### Interest Rate Swaps
```
Fixed leg value:
V_fixed = C × Σ DF(tᵢ) × τᵢ

Floating leg value (at reset):
V_float = 1 - DF(T)

Swap rate (par rate):
SR = [1 - DF(T)] / Σ DF(tᵢ) × τᵢ

Swap value:
V = (SR - K) × Annuity factor
```

### Swaptions
```
Option to enter swap

Payer swaption: Right to pay fixed
Receiver swaption: Right to receive fixed

Black's model:
V = A × [F × N(d₁) - K × N(d₂)]

Where:
- A = Annuity factor
- F = Forward swap rate
- σ = Swaption volatility
```

### Caps and Floors
```
Cap = Portfolio of caplets
Floor = Portfolio of floorlets

Caplet (Black's model):
Caplet = DF × τ × [F × N(d₁) - K × N(d₂)]

Cap-floor parity:
Cap - Floor = Swap (same K)
```

---

# SECTION 9: PORTFOLIO MATHEMATICS

## 9.1 Modern Portfolio Theory

### Two-Asset Portfolio
```
E[Rp] = w₁E[R₁] + w₂E[R₂]

σp² = w₁²σ₁² + w₂²σ₂² + 2w₁w₂σ₁σ₂ρ₁₂

Minimum variance portfolio:
w₁* = (σ₂² - σ₁σ₂ρ) / (σ₁² + σ₂² - 2σ₁σ₂ρ)
```

### N-Asset Portfolio
```
E[Rp] = w'μ

σp² = w'Σw

Where:
- w = Weight vector
- μ = Expected return vector
- Σ = Covariance matrix
```

### Efficient Frontier
```
Minimize: w'Σw
Subject to: w'μ = μ_target
           w'1 = 1

Lagrangian solution:
w* = Σ⁻¹ × [λ₁μ + λ₂1]

Frontier is hyperbola in (σ, E[R]) space
```

### Tangency Portfolio (Sharpe Ratio Maximization)
```
Maximize: (w'μ - rf) / √(w'Σw)

Solution:
w* = Σ⁻¹(μ - rf × 1) / 1'Σ⁻¹(μ - rf × 1)

Capital Market Line:
E[Rp] = rf + [(E[Rm] - rf) / σm] × σp
```

## 9.2 Factor Models

### Single-Factor (CAPM)
```
E[Ri] = rf + βi × (E[Rm] - rf)

Where:
βi = Cov(Ri, Rm) / Var(Rm)

Systematic risk: β × σm
Idiosyncratic risk: σε
Total: σi² = βi²σm² + σε²
```

### Multi-Factor (APT)
```
Ri = ai + bi₁F₁ + bi₂F₂ + ... + biₖFₖ + εi

Expected return:
E[Ri] = rf + bi₁λ₁ + bi₂λ₂ + ... + biₖλₖ

Where λj = Risk premium for factor j
```

### Fama-French Three-Factor
```
Ri - rf = αi + βi(Rm - rf) + si×SMB + hi×HML + εi

Where:
- SMB = Small minus Big (size factor)
- HML = High minus Low (value factor)

Extended to five factors:
+ RMW (profitability) + CMA (investment)
```

### Factor Risk Decomposition
```
Portfolio variance:
σp² = w'BΣFBw + w'Δw

Where:
- B = Factor loading matrix
- ΣF = Factor covariance matrix
- Δ = Idiosyncratic variance matrix

Factor contribution to risk:
Marginal contribution = ∂σp/∂wi
```

## 9.3 Risk Measures

### Value at Risk (VaR)
```
P(Loss > VaR) = α

Parametric VaR (normal):
VaR = μ - z_α × σ

Where z_α = Standard normal quantile

Example: 95% VaR with μ=10%, σ=20%
VaR = 10% - 1.645 × 20% = -22.9%
```

### Expected Shortfall (CVaR)
```
ES = E[Loss | Loss > VaR]

For normal distribution:
ES = μ + σ × φ(z_α) / α

Properties:
- Coherent risk measure
- Subadditive (diversification benefit)
- Better for fat tails
```

### Risk Decomposition
```
Marginal VaR:
MVaR_i = ∂VaR/∂wi = β_ip × VaR_p / w_i

Component VaR:
CVaR_i = wi × MVaR_i

Sum of component VaRs = Total VaR
```

---

# SECTION 10: FIXED INCOME ANALYTICS

## 10.1 Bond Mathematics

### Price-Yield Relationship
```
P = Σ[C/(1+y)^t] + F/(1+y)^n

Clean price: Quoted price
Dirty price: Clean + Accrued interest

Accrued = C × (Days since last coupon / Days in period)
```

### Yield Measures
```
Current yield = Annual coupon / Price

YTM: Rate that equates PV of cash flows to price

Yield to call: YTM assuming call exercise

Yield to worst: Minimum of all yields
```

### Spot and Forward Rates
```
Spot rate from bond prices:
P = C×DF(1) + C×DF(2) + ... + (C+F)×DF(n)
DF(t) = 1/(1+s_t)^t

Forward rate:
(1+s_2)² = (1+s_1)(1+f_{1,2})
f_{1,2} = (1+s_2)²/(1+s_1) - 1
```

## 10.2 Credit Instruments

### Credit Default Swaps
```
Protection buyer pays premium
Protection seller pays on credit event

Premium leg = Σ S × DF(tᵢ) × Δt × Survival(tᵢ)
Protection leg = Σ (1-R) × DF(tᵢ) × [Survival(tᵢ₋₁) - Survival(tᵢ)]

Par spread: Premium that equates legs
```

### Hazard Rate Model
```
Survival probability:
S(t) = e^(-∫₀^t λ(s)ds)

Constant hazard:
S(t) = e^(-λt)

Default probability:
PD(t) = 1 - S(t)

Hazard rate from spread:
λ ≈ Spread / (1 - R)
```

### Collateralized Debt Obligations
```
Tranche structure:
- Senior: Last loss, lowest yield
- Mezzanine: Middle loss, middle yield
- Equity: First loss, highest yield

Tranche valuation:
V = E[PV(Principal repayment + Interest - Losses)]

Key parameters:
- Default correlation
- Recovery rate
- Default probability
```

## 10.3 Mortgage-Backed Securities

### Prepayment Models
```
CPR = Conditional Prepayment Rate (annual)
SMM = Single Monthly Mortality

SMM = 1 - (1 - CPR)^(1/12)

PSA model:
CPR = 0.2% × min(month, 30) × PSA/100

Example: 150 PSA at month 20
CPR = 0.2% × 20 × 1.5 = 6%
```

### MBS Valuation
```
Price = Σ PV(Scheduled principal + Prepayments + Interest)

Option-adjusted spread (OAS):
Spread over benchmark after removing prepayment option value

OAS analysis:
- Monte Carlo simulation of rates
- Apply prepayment model
- Discount cash flows
- Find spread that matches price
```

### Effective Duration for MBS
```
Effective duration:
D_eff = (P₋ - P₊) / (2 × P₀ × Δy)

Where:
- P₋ = Price at lower yield
- P₊ = Price at higher yield
- Δy = Yield change

Negative convexity:
At lower yields, prepayments increase
Duration shortens as rates fall
```

---

# SECTION 11: BEHAVIORAL FINANCE MATHEMATICS

## 11.1 Prospect Theory

### Value Function
```
v(x) = x^α           for x ≥ 0
     = -λ(-x)^β      for x < 0

Typical parameters:
α = β ≈ 0.88
λ ≈ 2.25 (loss aversion coefficient)

Properties:
- Reference dependence
- Diminishing sensitivity
- Loss aversion (λ > 1)
```

### Probability Weighting
```
π(p) = p^γ / [p^γ + (1-p)^γ]^(1/γ)

Typical γ ≈ 0.61

Properties:
- Overweight small probabilities
- Underweight large probabilities
- Discontinuity at certainty
```

### Prospect Theory Value
```
V = Σ π(pᵢ) × v(xᵢ)

For simple gamble (x, p; y, 1-p):
V = π(p) × v(x) + π(1-p) × v(y)

Predicts:
- Risk seeking for losses
- Risk aversion for gains
- Preference reversal
```

## 11.2 Mental Accounting

### Narrow Framing
```
Evaluate each gamble separately:
U(G₁ + G₂) ≠ U(G₁) + U(G₂)

Implications:
- Equity premium puzzle
- Disposition effect
- House money effect
```

### Hedonic Editing
```
Combine outcomes to maximize pleasure:
- Segregate gains: v(x) + v(y) > v(x+y)
- Integrate losses: v(-x-y) > v(-x) + v(-y)
- Cancel loss with larger gain
- Segregate "silver linings"
```

## 11.3 Limits to Arbitrage

### Noise Trader Risk
```
DSSW Model:
Price = Fundamental + Noise trader demand effect

P_t = P* + μ_t + ρ_t

Where:
- P* = Fundamental value
- μ_t = Persistent mispricing
- ρ_t = Noise trader sentiment

Arbitrageur cannot eliminate mispricing due to:
- Noise trader risk
- Fundamental risk
- Implementation costs
```

### Synchronized Risk
```
Arbitrageurs face:
- Margin calls
- Withdrawal risk
- Career concerns

Optimal arbitrage position:
w* = (E[R] - rf) / (γ × σ² + λ × σ_sync²)

Adding synchronization risk reduces position
Mispricing can persist
```

---

# SECTION 12: MARKET MICROSTRUCTURE

## 12.1 Bid-Ask Spread Models

### Inventory Model (Stoll)
```
Spread = 2 × (Order processing + Inventory risk + Adverse selection)

Inventory-based spread:
S = 2σ√(τ/γ)

Where:
- σ = Price volatility
- τ = Time between trades
- γ = Risk tolerance
```

### Information Model (Kyle)
```
Single auction:
P = μ + λ × (x + u)

Where:
- μ = Prior value estimate
- λ = Price impact (Kyle's lambda)
- x = Informed order flow
- u = Noise trading

λ = σ_v / (2σ_u)

Informed trader profit = σ_v × σ_u / 2
```

### Glosten-Milgrom Model
```
Bid = E[V | Sell order]
Ask = E[V | Buy order]

Ask - Bid = 2 × π × (V_H - V_L) × P(Informed)

Where:
- π = Probability of informed trader
- V_H, V_L = High and low values
```

## 12.2 Price Impact Models

### Linear Price Impact
```
Price change = α + β × Sign(order) × √Volume

Permanent impact: Information component
Temporary impact: Liquidity component

Total cost = Permanent + Temporary
```

### Almgren-Chriss Model
```
Optimal execution minimizes:
E[Cost] + λ × Var[Cost]

Optimal trajectory:
x_t = X × sinh[κ(T-t)] / sinh[κT]

Where:
- X = Total shares
- κ = Trade-off parameter
- Faster execution = Higher impact cost
- Slower execution = Higher volatility risk
```

### Square Root Law
```
Price impact ∝ √(Volume / Average Daily Volume)

Empirical relationship:
ΔP/P ≈ σ × √(V/V_daily) / √(Spread/Tick)
```

## 12.3 High-Frequency Dynamics

### Order Flow Toxicity
```
VPIN (Volume-Synchronized PIN):
VPIN = |V_buy - V_sell| / (V_buy + V_sell)

High VPIN indicates:
- Informed trading
- Adverse selection risk
- Market maker vulnerability
```

### Latency Arbitrage
```
Profit opportunity:
Δ = (P_fast - P_slow) × Position

Conditional on:
- Information arrives at fast venue
- Slow venue hasn't updated
- Transaction costs < Δ

Speed advantage matters for:
- Cross-venue arbitrage
- Index arbitrage
- Statistical arbitrage
```

---

# SECTION 13: CRYPTOCURRENCY MATHEMATICS

## 13.1 Bitcoin Economics

### Mining Economics
```
Block reward schedule:
Reward = 50 × (1/2)^⌊height/210000⌋

Current (2024): 3.125 BTC per block
Halving every ~4 years

Mining profitability:
Profit = Block reward × Price - Electricity - Hardware - Pool fees
       = (Hashrate/Network hashrate) × Reward × Price - Costs
```

### Difficulty Adjustment
```
Target block time: 10 minutes

Difficulty adjustment (every 2016 blocks):
New difficulty = Old × (2016 × 10 min) / Actual time

Maximum adjustment: 4× up or 0.25× down

Network security:
Cost to 51% attack ≈ 0.5 × Block reward × Blocks × Time
```

### Stock-to-Flow Model
```
S2F = Stock / Annual Flow

Bitcoin S2F = Current supply / Annual issuance
            ≈ 19M / 0.164M ≈ 116 (post-2024 halving)

Price model (PlanB):
ln(Price) = a × ln(S2F) + b

Criticized but influential
```

## 13.2 DeFi Mathematics

### Automated Market Makers
```
Constant product formula (Uniswap v2):
x × y = k

Price:
P = y / x (price of x in terms of y)

After trade (buy Δx of token x):
(x - Δx)(y + Δy) = k
Δy = k/(x - Δx) - y

Price impact = Δy/Δx vs spot price
```

### Impermanent Loss
```
IL = 2√r / (1 + r) - 1

Where r = Price ratio change

Example:
Price doubles (r = 2):
IL = 2√2 / 3 - 1 ≈ -5.7%

LP return = Fees - IL
Profitable if fees > IL
```

### Yield Farming Mathematics
```
APY from APR:
APY = (1 + APR/n)^n - 1

With continuous compounding:
APY = e^APR - 1

Real yield considerations:
- Token inflation
- IL
- Smart contract risk
- Gas costs
```

### Liquidation Mechanics
```
Health factor:
HF = (Collateral × Liquidation threshold) / Debt

Liquidation when HF < 1

Liquidation penalty:
Liquidator receives collateral at discount
Borrower pays penalty (typically 5-15%)

Safe collateralization ratio:
CR = Collateral / Debt > 1 / LT + Buffer
```

## 13.3 Token Economics

### Bonding Curves
```
Price function of supply:
P(S) = f(S)

Linear: P = a × S
Polynomial: P = a × S^n
Exponential: P = a × e^(bS)

Reserve ratio:
RR = Reserve / (S × P(S))

Bancor formula:
P = Reserve / (Supply × RR)
```

### Token Velocity
```
MV = PQ (Fisher equation for tokens)

Value capture:
V = PQ / M × (1/velocity)

High velocity = Low value capture
Reduce velocity via:
- Staking
- Governance utility
- Time locks
```

---

# SECTION 14: REAL ESTATE FINANCE

## 14.1 Property Valuation

### Income Approach
```
Direct capitalization:
Value = NOI / Cap rate

Where:
NOI = Effective Gross Income - Operating Expenses
Cap rate = Market-derived from comparables

DCF approach:
Value = Σ NOI_t/(1+r)^t + Terminal/(1+r)^n
```

### Cap Rate Decomposition
```
Cap rate = Discount rate - Growth rate
         = Risk-free + Risk premium - Expected NOI growth

Gordon model relationship:
Value = NOI / (r - g)
Cap rate = r - g
```

### Gross Rent Multiplier
```
GRM = Property price / Annual gross rent

Quick valuation:
Value = GRM × Annual rent

Limitation: Ignores expenses and vacancy
```

## 14.2 Mortgage Mathematics

### Mortgage Payment Calculation
```
Monthly payment:
PMT = P × r(1+r)^n / [(1+r)^n - 1]

Where:
- P = Principal
- r = Monthly rate
- n = Number of payments

Example: $300,000, 6%, 30 years
PMT = 300000 × 0.005 × 1.005^360 / (1.005^360 - 1)
    = $1,798.65
```

### Amortization Schedule
```
Month t:
Interest_t = Balance_{t-1} × r
Principal_t = PMT - Interest_t
Balance_t = Balance_{t-1} - Principal_t

Early payments mostly interest
Later payments mostly principal
```

### Loan-to-Value and Debt Service Coverage
```
LTV = Loan amount / Property value
     Target: < 80% (conventional)

DSCR = NOI / Debt service
     Target: > 1.25

Maximum loan from DSCR:
Max loan = NOI / (Target DSCR × Annual debt service factor)
```

## 14.3 REIT Analysis

### Funds from Operations (FFO)
```
FFO = Net income
    + Depreciation/Amortization
    - Gains on property sales
    + Losses on property sales

AFFO = FFO
     - Recurring capex
     - Straight-line rent adjustments
```

### REIT Valuation
```
Price/FFO multiple:
Compare to sector peers

NAV approach:
NAV = Market value of properties - Liabilities

Premium/discount to NAV:
(Price - NAV) / NAV

Dividend yield:
REITs must distribute 90% of taxable income
```

---

# SECTION 15: PRIVATE EQUITY MATHEMATICS

## 15.1 LBO Mechanics

### Sources and Uses
```
USES:
- Purchase price (Enterprise value)
- Transaction fees
- Refinancing existing debt

SOURCES:
- Senior debt
- Subordinated debt / Mezzanine
- Equity contribution

Equity = Uses - Debt raised
```

### LBO Returns
```
IRR calculation:
-Equity₀ + Σ CF_t/(1+IRR)^t + Exit/(1+IRR)^n = 0

Cash-on-cash multiple (MOIC):
MOIC = (Total distributions + Exit value) / Invested capital

Value creation:
- EBITDA growth
- Multiple expansion
- Debt paydown
```

### Debt Capacity
```
Senior debt: 3-4× EBITDA (typical)
Total debt: 5-6× EBITDA

Interest coverage test:
EBITDA / Interest > 2×

Fixed charge coverage:
(EBITDA - Capex) / (Interest + Mandatory principal) > 1×
```

## 15.2 Venture Capital

### Pre-Money and Post-Money
```
Post-money = Pre-money + Investment

Ownership:
Investor % = Investment / Post-money
Founder % = Pre-money / Post-money
```

### Option Pool
```
Pre-money including option pool:
Effective pre-money = Stated pre-money - Option pool value

Dilution:
New founder % = (1 - Investor %) × (1 - Option pool %)
```

### Liquidation Preferences
```
1× non-participating:
Investor receives: max(Investment, % × Exit)

1× participating with cap:
Investor receives: min(Investment + % × (Exit - Investment), Cap × Investment)

Participating preferred:
Investment + % × (Exit - Investment)

Conversion:
Convert when: % × Exit > Preference amount
```

## 15.3 Fund Economics

### Carried Interest (2 and 20)
```
Management fee: 2% of committed capital (typically)
Carry: 20% of profits above hurdle

Waterfall:
1. Return of capital
2. Preferred return (hurdle, ~8%)
3. GP catch-up (to reach 20% of profits)
4. 80/20 split

Example: $100M fund, 2× exit, 8% hurdle
Return = $200M
Hurdle = $100M × 1.08^5 = $147M (over 5 years)
Profit above hurdle = $53M
GP carry = $53M × 20% = $10.6M
```

### J-Curve Effect
```
Early years: Negative returns
- Management fees
- Investment period
- No exits yet

Middle years: Exits begin
- Positive cash flows
- IRR turns positive

Late years: Final exits
- Remaining value realized
```

---

# SECTION 16: INSURANCE MATHEMATICS

## 16.1 Life Insurance Pricing

### Mortality Tables
```
qₓ = Probability of death at age x
pₓ = 1 - qₓ = Survival probability

Life expectancy:
eₓ = Σ ₜpₓ (sum over all future years)

ₜpₓ = p_x × p_{x+1} × ... × p_{x+t-1}
```

### Present Value of Life Annuity
```
äₓ = Σ vᵗ × ₜpₓ (from t=0 to ω-x)

Where:
- v = 1/(1+i) = Discount factor
- ω = Maximum age

Continuous:
āₓ = ∫₀^∞ e^(-δt) × ₜpₓ dt
```

### Term Life Insurance
```
Net single premium for n-year term:
A¹ₓ:n = Σ vᵗ⁺¹ × ₜpₓ × q_{x+t} (from t=0 to n-1)

Level annual premium:
P = A¹ₓ:n / äₓ:n
```

### Whole Life Insurance
```
Net single premium:
Aₓ = Σ vᵗ⁺¹ × ₜpₓ × q_{x+t} (from t=0 to ω-x)

Annual premium:
P = Aₓ / äₓ
```

## 16.2 Property & Casualty

### Loss Distributions
```
Frequency: Number of claims
- Poisson: P(N=k) = e^(-λ) × λᵏ / k!
- Negative binomial: Overdispersed counts

Severity: Size of each claim
- Lognormal
- Pareto: Heavy tail
- Gamma

Aggregate loss:
S = X₁ + X₂ + ... + Xₙ

E[S] = E[N] × E[X]
Var[S] = E[N] × Var[X] + Var[N] × E[X]²
```

### Loss Reserving
```
Development triangle:
       1    2    3    4   Ultimate
2019  100  150  170  180   180
2020  110  165  187        ?
2021  105  158             ?
2022  115                  ?

Chain ladder method:
Development factor = Σ C_{i,k+1} / Σ C_{i,k}

Ultimate = Current × Development factor
```

### Reinsurance Pricing
```
Excess of loss:
Recoverable = min(max(Loss - Attachment, 0), Limit)

Expected recovery:
E[Recovery] = ∫ᵃᵃ⁺ˡ (x-a)f(x)dx + l × P(X > a+l)

Where:
- a = Attachment point
- l = Limit
- f(x) = Loss density
```

## 16.3 Risk-Based Capital

### RBC Ratio
```
RBC Ratio = Total Adjusted Capital / Risk-Based Capital requirement

RBC components (life):
- C0: Asset/affiliate risk
- C1: Asset risk (invested)
- C2: Insurance risk
- C3: Interest rate risk
- C4: Business risk

Total RBC = √(C0² + C1² + C2² + C3² + C4²)
(Covariance adjustment)
```

### Regulatory Action Levels
```
>200%: No action
150-200%: Company action level
100-150%: Regulatory action level
70-100%: Authorized control level
<70%: Mandatory control level
```

---

# SECTION 17: COMMODITY MARKETS

## 17.1 Futures Pricing

### Cost of Carry Model
```
F = S × e^((r + u - y) × T)

Where:
- S = Spot price
- r = Risk-free rate
- u = Storage cost (as yield)
- y = Convenience yield

For financial futures (no storage, no convenience):
F = S × e^(r × T)
```

### Contango and Backwardation
```
Contango: F > S
- Futures price above spot
- Normal for storable commodities
- Cost of carry positive

Backwardation: F < S
- Futures price below spot
- Convenience yield high
- Supply shortages
```

### Roll Yield
```
Roll yield = (Near month price - Far month price) / Near month price

Backwardated market: Positive roll yield
Contango market: Negative roll yield

Total return = Spot return + Roll yield + Collateral yield
```

## 17.2 Energy Markets

### Crack Spread
```
Simple crack spread (3-2-1):
Profit = 2 × Gasoline + 1 × Heating oil - 3 × Crude oil
       (per barrel)

Refining margin:
Crack = (Product revenues - Crude cost) / Crude volume
```

### Natural Gas Basis
```
Basis = Regional price - Henry Hub price

Basis risk:
- Transportation constraints
- Regional supply/demand
- Seasonal patterns

Hedging:
Physical delivery at location ≠ Futures delivery point
```

### Spark Spread (Power)
```
Spark spread = Power price - (Gas price × Heat rate)

Heat rate = BTU input / kWh output
Efficient plant: ~7,000 BTU/kWh

Dark spread (coal):
Dark spread = Power price - (Coal price × Heat rate)
```

## 17.3 Agricultural Commodities

### Crop Year Spreads
```
Old crop: Near month (current crop year)
New crop: Deferred month (next harvest)

Spread reflects:
- Current supply tightness
- Expected harvest
- Storage dynamics

Inverse spread: Old > New (supply shortage)
Carry spread: New > Old (normal)
```

### Weather Derivatives
```
Heating Degree Days (HDD):
HDD = max(65°F - T_avg, 0)

Cooling Degree Days (CDD):
CDD = max(T_avg - 65°F, 0)

Contract payoff:
Payoff = Notional × (Actual DD - Strike DD)

Used by utilities, agriculture
```

---

# SECTION 18: FINANCIAL ECONOMETRICS

## 18.1 Time Series Models

### ARIMA Models
```
AR(p): yₜ = c + φ₁yₜ₋₁ + ... + φₚyₜ₋ₚ + εₜ
MA(q): yₜ = c + εₜ + θ₁εₜ₋₁ + ... + θqεₜ₋q
ARMA(p,q): Combination

Stationarity condition (AR):
Roots of 1 - φ₁z - ... - φₚzᵖ = 0 outside unit circle

Box-Jenkins methodology:
1. Identification (ACF, PACF)
2. Estimation (MLE)
3. Diagnostic checking
4. Forecasting
```

### Unit Root Tests
```
Dickey-Fuller test:
H₀: ρ = 1 (unit root)
Δyₜ = α + (ρ-1)yₜ₋₁ + εₜ

Augmented Dickey-Fuller:
Δyₜ = α + (ρ-1)yₜ₋₁ + Σγᵢ Δyₜ₋ᵢ + εₜ

Critical values: Non-standard distribution
```

### Cointegration
```
Two I(1) series cointegrated if linear combination is I(0)

Engle-Granger test:
1. Regress y on x
2. Test residuals for unit root
3. If residuals stationary → Cointegrated

Error correction model:
Δyₜ = α(yₜ₋₁ - βxₜ₋₁) + εₜ

α = Speed of adjustment
```

## 18.2 Volatility Models

### ARCH/GARCH
```
ARCH(q):
σₜ² = ω + Σαᵢεₜ₋ᵢ²

GARCH(p,q):
σₜ² = ω + Σαᵢεₜ₋ᵢ² + Σβⱼσₜ₋ⱼ²

Persistence: Σαᵢ + Σβⱼ

GARCH(1,1):
σₜ² = ω + αεₜ₋₁² + βσₜ₋₁²
Unconditional variance: ω / (1 - α - β)
```

### EGARCH
```
ln(σₜ²) = ω + α[|εₜ₋₁/σₜ₋₁| - E|εₜ₋₁/σₜ₋₁|] + γ(εₜ₋₁/σₜ₋₁) + β ln(σₜ₋₁²)

Advantages:
- No positivity constraints
- Asymmetric effects (γ term)
- Leverage effect: γ < 0
```

### GJR-GARCH
```
σₜ² = ω + αεₜ₋₁² + γεₜ₋₁²Iₜ₋₁ + βσₜ₋₁²

Where Iₜ₋₁ = 1 if εₜ₋₁ < 0

Captures leverage effect:
Negative shocks increase volatility more
```

## 18.3 Event Studies

### Abnormal Return Calculation
```
Market model:
Rᵢₜ = αᵢ + βᵢRₘₜ + εᵢₜ

Estimate over estimation window

Abnormal return:
ARᵢₜ = Rᵢₜ - (α̂ᵢ + β̂ᵢRₘₜ)

Cumulative abnormal return:
CAR = Σ AR (over event window)
```

### Statistical Significance
```
Test statistic:
t = CAR / √(Var[CAR])

Cross-sectional test:
CAAR = (1/N) Σ CARᵢ
t = CAAR / (s / √N)

Adjustments:
- Event-induced variance
- Cross-sectional correlation
- Thin trading
```

---

# SECTION 19: FINANCIAL REGULATION

## 19.1 Capital Requirements

### Basel III Summary
```
Capital:
- CET1 ≥ 4.5%
- Tier 1 ≥ 6%
- Total ≥ 8%

Buffers:
- Conservation: 2.5%
- Countercyclical: 0-2.5%
- G-SIB: 1-3.5%

Effective minimum for G-SIBs: 9.5-15%
```

### Leverage Ratio
```
Leverage ratio = Tier 1 capital / Exposure measure ≥ 3%

Exposure measure:
- On-balance sheet assets
- Derivative exposures
- SFT exposures
- Off-balance sheet items
```

### Stress Testing
```
CCAR/DFAST (US):
- Severely adverse scenario
- Adverse scenario
- Baseline scenario

Capital trajectory:
Project capital ratios under stress

Qualitative assessment:
- Risk management
- Capital planning process
```

## 19.2 Market Regulation

### Securities Laws
```
1933 Act: Securities registration
1934 Act: Secondary markets, broker-dealers
Investment Advisers Act 1940
Investment Company Act 1940
Dodd-Frank 2010

Exemptions:
- Private placements (Reg D)
- Accredited investors
- Qualified institutional buyers (144A)
```

### Market Structure Rules
```
Reg NMS (US equities):
- Order protection rule
- Access rule
- Sub-penny rule
- Market data rules

MiFID II (Europe):
- Best execution
- Transparency
- Unbundling
- Trading venue categories
```

## 19.3 Systemic Risk

### Systemically Important Institutions
```
G-SIB indicators:
- Size
- Interconnectedness
- Substitutability
- Complexity
- Cross-jurisdictional activity

TBTF problem:
Implicit guarantee → Moral hazard → Excessive risk-taking

Solutions:
- Higher capital
- Resolution planning
- Ring-fencing
```

### Macroprudential Tools
```
Countercyclical capital buffer:
Increase in boom, release in bust

Loan-to-value caps:
Limit mortgage leverage

Debt-to-income limits:
Affordability constraints

Sectoral capital requirements:
Target specific exposures
```

---

# SECTION 20: QUANTITATIVE TRADING

## 20.1 Backtesting Framework

### Performance Metrics
```
Sharpe ratio:
SR = (E[R] - rf) / σ(R)

Sortino ratio:
So = (E[R] - rf) / σ_downside

Maximum drawdown:
MDD = max(Peak - Trough) / Peak

Calmar ratio:
Calmar = Annual return / MDD
```

### Backtesting Pitfalls
```
Look-ahead bias:
Using future information in past decisions

Survivorship bias:
Only testing on surviving securities

Data snooping:
Multiple testing without adjustment

Overfitting:
Too many parameters, too little data

Out-of-sample testing essential
Walk-forward analysis
```

### Transaction Cost Modeling
```
Explicit costs:
- Commission
- Exchange fees
- Taxes

Implicit costs:
- Bid-ask spread
- Market impact
- Opportunity cost

Total cost = Half spread + Impact + Timing cost

Impact model:
I = σ × √(V/ADV) × Sign(order)
```

## 20.2 Statistical Arbitrage

### Pairs Trading
```
Cointegration-based:
y_t - β × x_t = spread_t ~ I(0)

Signal:
z_t = (spread_t - mean) / std

Trade rules:
- Enter long spread: z < -threshold
- Enter short spread: z > +threshold
- Exit: z returns to 0
```

### Mean Reversion Testing
```
Ornstein-Uhlenbeck process:
dX = θ(μ - X)dt + σdW

Half-life of mean reversion:
t_{1/2} = ln(2) / θ

Estimate θ from regression:
ΔX = θ(μ - X_{t-1}) + ε
```

### Factor-Based Strategies
```
Momentum:
Long winners, short losers
12-month return, skip recent month

Value:
Long cheap, short expensive
Book-to-market, earnings yield

Quality:
Long profitable, short unprofitable
ROE, accruals

Size:
Small minus big
Market cap based
```

## 20.3 Execution Algorithms

### TWAP
```
Time-Weighted Average Price:
Execute equal amounts over time

Slice size = Total / Number of intervals
Execute each slice at market

Benchmark: TWAP during execution period
```

### VWAP
```
Volume-Weighted Average Price:
Execute proportional to expected volume

Slice_t = Total × (Expected volume_t / Total volume)

Volume profile from historical data
Intraday U-shape typical
```

### Implementation Shortfall
```
IS = (Execution price - Decision price) × Quantity

Components:
- Delay cost
- Market impact
- Timing cost
- Opportunity cost

Minimize:
E[IS] + λ × Var[IS]

Leads to Almgren-Chriss optimal trajectory
```

---

# QUICK REFERENCE

## Key Formulas

### Valuation
```
DCF: V = Σ FCF_t/(1+r)^t + TV/(1+r)^n
Gordon Growth: V = D₁/(r-g)
WACC: r = (E/V)×re + (D/V)×rd×(1-T)
```

### Options
```
Black-Scholes Call: C = SN(d₁) - Ke^(-rT)N(d₂)
Put-Call Parity: C + Ke^(-rT) = P + S
Delta (call): N(d₁)
```

### Risk
```
VaR (normal): μ - z_α × σ
Beta: Cov(Ri,Rm)/Var(Rm)
Sharpe: (E[R]-rf)/σ
```

### Fixed Income
```
Duration: -∂P/∂y × (1/P)
Convexity: ∂²P/∂y² × (1/P)
Yield: Σ CF/(1+y)^t = Price
```

## Important Numbers
```
Risk-free proxy: 10-year Treasury
Equity premium: ~5-6% (historical)
Beta market: 1.0
Typical Sharpe: 0.3-0.5 (good funds)
Basel CET1: 4.5% + buffers
Fed funds neutral: r* + 2% inflation
```

---

*Advanced money knowledge for computational systems*
