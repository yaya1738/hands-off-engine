# BUSINESS KNOWLEDGE - ADVANCED
## Deep Technical Internals

*The hidden depths of business - models, mathematics, and strategic frameworks*

---

# TABLE OF CONTENTS

1. [Microeconomics Deep Dive](#1-microeconomics-deep-dive)
2. [Macroeconomics Internals](#2-macroeconomics-internals)
3. [Financial Statement Analysis](#3-financial-statement-analysis)
4. [Valuation Mathematics](#4-valuation-mathematics)
5. [Options & Derivatives](#5-options--derivatives)
6. [Portfolio Theory](#6-portfolio-theory)
7. [Behavioral Economics](#7-behavioral-economics)
8. [Game Theory in Business](#8-game-theory-in-business)
9. [Market Microstructure](#9-market-microstructure)
10. [Corporate Governance Internals](#10-corporate-governance-internals)
11. [M&A Mechanics](#11-ma-mechanics)
12. [Private Equity & Venture Capital](#12-private-equity--venture-capital)
13. [Tax Strategy](#13-tax-strategy)
14. [Negotiation Science](#14-negotiation-science)
15. [Organizational Design](#15-organizational-design)
16. [Innovation Management](#16-innovation-management)
17. [Business Model Mechanics](#17-business-model-mechanics)
18. [Network Effects & Platform Economics](#18-network-effects--platform-economics)
19. [Pricing Science](#19-pricing-science)
20. [Decision Theory](#20-decision-theory)

---

# 1. MICROECONOMICS DEEP DIVE

## 1.1 Consumer Theory

### Utility Functions
```
Cardinal Utility: U(x, y) = actual numerical value
Ordinal Utility: Ranking of preferences

Common Forms:
  Cobb-Douglas: U = x^a × y^b
  Perfect Substitutes: U = ax + by
  Perfect Complements: U = min(ax, by)
  Quasilinear: U = v(x) + y
```

### Utility Maximization
```
Problem:
  max U(x, y)
  subject to: Px·x + Py·y ≤ M

Lagrangian:
  L = U(x, y) + λ(M - Px·x - Py·y)

First Order Conditions:
  ∂L/∂x = ∂U/∂x - λPx = 0
  ∂L/∂y = ∂U/∂y - λPy = 0
  ∂L/∂λ = M - Px·x - Py·y = 0

Solution: MRS = Px/Py
  (Marginal Rate of Substitution = Price ratio)
```

### Demand Functions
```
Marshallian Demand:
  x*(Px, Py, M) - Quantity demanded given prices and income

Hicksian Demand:
  x^h(Px, Py, U) - Compensated demand (constant utility)

Slutsky Equation:
  ∂x/∂Px = ∂x^h/∂Px - x·(∂x/∂M)
  Total effect = Substitution effect + Income effect
```

### Elasticity Formulas
```
Price Elasticity of Demand:
  Ed = (∂Q/∂P) × (P/Q) = (% ΔQ) / (% ΔP)

Income Elasticity:
  Ey = (∂Q/∂Y) × (Y/Q)

Cross-Price Elasticity:
  Exy = (∂Qx/∂Py) × (Py/Qx)

Arc Elasticity:
  Ed = [(Q2-Q1)/((Q1+Q2)/2)] / [(P2-P1)/((P1+P2)/2)]
```

## 1.2 Producer Theory

### Production Functions
```
General: Q = f(K, L)

Cobb-Douglas: Q = A·K^α·L^β
  - Returns to scale: α + β
  - α + β > 1: Increasing returns
  - α + β = 1: Constant returns
  - α + β < 1: Decreasing returns

Marginal Products:
  MPL = ∂Q/∂L
  MPK = ∂Q/∂K

MRTS (Marginal Rate of Technical Substitution):
  MRTS = MPL/MPK = -dK/dL
```

### Cost Minimization
```
Problem:
  min C = wL + rK
  subject to: f(K, L) = Q

Solution: MRTS = w/r
  (Ratio of marginal products = Input price ratio)

Cost Function:
  C(Q, w, r) - Minimum cost to produce Q

Short-run vs Long-run:
  Short-run: Some inputs fixed
  Long-run: All inputs variable
```

### Cost Curves
```
Total Cost: TC = FC + VC
Average Total Cost: ATC = TC/Q
Average Variable Cost: AVC = VC/Q
Average Fixed Cost: AFC = FC/Q
Marginal Cost: MC = dTC/dQ

Relationships:
  - MC intersects ATC and AVC at minimum
  - When MC < ATC, ATC is falling
  - When MC > ATC, ATC is rising
```

## 1.3 Market Equilibrium

### Perfect Competition Long-run
```
Zero economic profit:
  P = MC = ATC (minimum)

Industry supply:
  Horizontal sum of firm supply curves

Long-run adjustment:
  - Profit → Entry → Supply shifts right → Price falls
  - Loss → Exit → Supply shifts left → Price rises
```

### Monopoly Optimization
```
Profit: π = TR - TC = P(Q)·Q - C(Q)

Maximize:
  dπ/dQ = MR - MC = 0
  MR = MC

Marginal Revenue:
  MR = P + Q·(dP/dQ) = P(1 - 1/|Ed|)

Lerner Index (Markup):
  L = (P - MC)/P = 1/|Ed|

Dead Weight Loss:
  DWL = ½ × (Pm - MC) × (Qc - Qm)
```

### Oligopoly Models
```
Cournot (Quantity Competition):
  - Firms choose quantities simultaneously
  - Nash equilibrium in quantities

Bertrand (Price Competition):
  - Firms choose prices simultaneously
  - Tends to competitive outcome

Stackelberg (Leader-Follower):
  - Leader commits first
  - Follower responds optimally
  - Leader has first-mover advantage
```

---

# 2. MACROECONOMICS INTERNALS

## 2.1 National Income Accounting

### GDP Calculation
```
Expenditure Approach:
  GDP = C + I + G + (X - M)

Income Approach:
  GDP = Wages + Rent + Interest + Profits + Depreciation + Indirect taxes

Real vs Nominal:
  Real GDP = Nominal GDP / GDP Deflator × 100
  GDP Deflator = (Nominal GDP / Real GDP) × 100
```

### Key Identities
```
National Savings:
  S = Y - C - G = I + NX

Private Savings:
  Sp = Y - T - C

Public Savings:
  Sg = T - G

Trade Balance:
  NX = X - M = S - I
```

## 2.2 IS-LM Model

### IS Curve (Goods Market)
```
Equilibrium: Y = C + I + G

Where:
  C = C0 + c(Y - T)
  I = I0 - bi

IS Equation:
  Y = [C0 + I0 + G - cT] × (1/(1-c)) - (b/(1-c))×i

Slope: Negative (higher i → lower I → lower Y)
```

### LM Curve (Money Market)
```
Money demand: L = kY - hi
Money supply: M/P

Equilibrium:
  M/P = kY - hi

LM Equation:
  i = (k/h)Y - (1/h)(M/P)

Slope: Positive (higher Y → higher L → higher i)
```

### Equilibrium
```
Intersection of IS and LM

Policy Effects:
  - Fiscal expansion: IS shifts right → Y↑, i↑
  - Monetary expansion: LM shifts right → Y↑, i↓

Crowding Out:
  Government spending raises i, reduces private I
```

## 2.3 AD-AS Model

### Aggregate Demand
```
Derived from IS-LM

AD shifts right:
  - Increase in G
  - Decrease in T
  - Increase in M
  - Increase in confidence
```

### Aggregate Supply
```
Short-run AS (SRAS):
  P = Pe + α(Y - Y*)
  Upward sloping (sticky wages/prices)

Long-run AS (LRAS):
  Vertical at Y* (potential output)
  Based on capital, labor, technology
```

### Phillips Curve
```
Original:
  Unemployment vs Inflation tradeoff

Expectations-Augmented:
  π = πe - β(u - u*) + supply shocks

NAIRU: Non-Accelerating Inflation Rate of Unemployment
  When u = u*, inflation stable at expected rate
```

## 2.4 Growth Theory

### Solow Growth Model
```
Production: Y = F(K, L) = K^α × L^(1-α)

Per worker: y = k^α
  Where y = Y/L, k = K/L

Capital Accumulation:
  Δk = sy - (n + δ)k
  s = savings rate
  n = population growth
  δ = depreciation

Steady State:
  sy* = (n + δ)k*
  k* = (s/(n+δ))^(1/(1-α))

Golden Rule:
  Maximize consumption: MPK = n + δ
```

### Endogenous Growth
```
AK Model:
  Y = AK
  No diminishing returns
  Growth rate = sA - δ

R&D Models:
  - Ideas drive growth
  - Increasing returns to scale
  - Government policy matters
```

---

# 3. FINANCIAL STATEMENT ANALYSIS

## 3.1 Advanced Ratio Analysis

### DuPont Analysis
```
ROE = Net Income / Equity

3-Factor DuPont:
  ROE = (Net Income/Sales) × (Sales/Assets) × (Assets/Equity)
      = Net Profit Margin × Asset Turnover × Equity Multiplier

5-Factor DuPont:
  ROE = (EBIT/Sales) × (Sales/Assets) × (Assets/Equity) ×
        (EBT/EBIT) × (Net Income/EBT)
      = Operating Margin × Asset Turnover × Leverage ×
        Interest Burden × Tax Burden
```

### Sustainable Growth Rate
```
g = ROE × b

Where:
  g = Sustainable growth rate
  b = Retention ratio (1 - Dividend payout ratio)

g = (NI/Equity) × (1 - Dividends/NI)
```

### Z-Score (Bankruptcy Prediction)
```
Altman Z-Score:

Z = 1.2(WC/TA) + 1.4(RE/TA) + 3.3(EBIT/TA) +
    0.6(MVE/BVL) + 1.0(Sales/TA)

Where:
  WC = Working Capital
  TA = Total Assets
  RE = Retained Earnings
  MVE = Market Value of Equity
  BVL = Book Value of Liabilities

Interpretation:
  Z > 2.99: Safe
  1.81 < Z < 2.99: Grey zone
  Z < 1.81: Distress
```

## 3.2 Cash Flow Analysis

### Free Cash Flow
```
Free Cash Flow to Firm (FCFF):
  FCFF = EBIT(1-T) + D&A - CapEx - ΔNWC

Free Cash Flow to Equity (FCFE):
  FCFE = Net Income + D&A - CapEx - ΔNWC + Net Borrowing
       = FCFF - Interest(1-T) + Net Borrowing

Unlevered Free Cash Flow:
  Same as FCFF (excludes financing effects)
```

### Cash Flow Ratios
```
Operating Cash Flow Ratio:
  CFO / Current Liabilities

Cash Flow Margin:
  CFO / Revenue

Cash Return on Assets:
  CFO / Total Assets

Free Cash Flow Yield:
  FCF / Market Cap
```

## 3.3 Earnings Quality

### Red Flags
```
Accruals Analysis:
  High accruals vs cash flow = Lower quality

Accruals = Net Income - Operating Cash Flow

Accrual Ratio:
  (NOA_t - NOA_{t-1}) / Average NOA
  Higher ratio = More aggressive accounting

Revenue Recognition Issues:
  - Growing receivables faster than sales
  - Unusual deferred revenue changes
  - Inconsistent revenue patterns

Expense Manipulation:
  - Capitalization vs expensing
  - Reserve manipulation
  - One-time charges
```

### Quality of Earnings Adjustments
```
Normalized Earnings:
  - Remove non-recurring items
  - Adjust for accounting choices
  - Consider economic substance

Pro Forma Earnings:
  - Exclude certain expenses
  - Compare to GAAP carefully
```

---

# 4. VALUATION MATHEMATICS

## 4.1 DCF Deep Dive

### Multi-Stage DCF
```
Stage 1: Explicit forecast (5-10 years)
  PV1 = Σ [FCF_t / (1 + WACC)^t]

Stage 2: Transition period (optional)
  Declining growth to stable rate

Stage 3: Terminal value
  TV = FCF_n × (1 + g) / (WACC - g)
  PV_TV = TV / (1 + WACC)^n

Enterprise Value = PV1 + PV_TV
Equity Value = EV - Net Debt
Price per Share = Equity Value / Shares Outstanding
```

### Sensitivity Analysis
```
Key Drivers:
  - Revenue growth rate
  - Operating margin
  - WACC
  - Terminal growth rate

Tornado Diagram:
  Show impact of each variable on value

Monte Carlo Simulation:
  - Assign distributions to inputs
  - Run thousands of scenarios
  - Output probability distribution of value
```

## 4.2 Comparable Analysis Details

### Multiple Selection
```
Revenue Multiples (EV/Revenue):
  - Early-stage, unprofitable
  - High-growth companies
  - Industry: SaaS typically 5-15x

EBITDA Multiples (EV/EBITDA):
  - Most common
  - Capital-intensive industries
  - Typical: 6-12x

Earnings Multiples (P/E):
  - Mature, profitable companies
  - Easy to understand
  - Typical: 15-25x

Book Value (P/B):
  - Financial institutions
  - Asset-heavy businesses
```

### Adjustments
```
Normalize for:
  - Non-recurring items
  - Different fiscal years
  - Different accounting policies
  - Cyclical adjustments

Control Premium:
  - Add 20-40% for control
  - Precedent transactions include premium

Liquidity Discount:
  - Subtract 20-30% for private companies
  - Illiquidity adjustment
```

## 4.3 Sum of the Parts (SOTP)
```
For diversified companies:

1. Separate business segments
2. Value each segment independently
3. Apply appropriate multiple for each
4. Sum segment values
5. Subtract corporate overhead
6. Add non-operating assets
7. Subtract net debt

Conglomerate Discount:
  - Market values below SOTP
  - Typically 10-20%
```

## 4.4 Option-Based Valuation

### Real Options
```
Types:
  - Option to expand
  - Option to abandon
  - Option to delay
  - Option to switch

Black-Scholes Framework:
  - Underlying: PV of cash flows
  - Strike: Investment required
  - Time: Duration of option
  - Volatility: Uncertainty in cash flows
  - Risk-free rate: Time value

Binomial Model:
  - Discrete time steps
  - Up/down movements
  - Work backwards from payoffs
```

---

# 5. OPTIONS & DERIVATIVES

## 5.1 Option Basics

### Payoff Diagrams
```
Call Option:
  Payoff = max(S - K, 0)
  Profit = max(S - K, 0) - Premium

Put Option:
  Payoff = max(K - S, 0)
  Profit = max(K - S, 0) - Premium

Where:
  S = Stock price at expiration
  K = Strike price
```

### Put-Call Parity
```
C + PV(K) = P + S

Where:
  C = Call price
  P = Put price
  K = Strike price
  S = Stock price

Rearranged:
  C - P = S - PV(K)
```

## 5.2 Black-Scholes Model

### Formula
```
Call: C = S·N(d1) - K·e^(-rT)·N(d2)
Put:  P = K·e^(-rT)·N(-d2) - S·N(-d1)

Where:
  d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
  d2 = d1 - σ√T

Parameters:
  S = Current stock price
  K = Strike price
  r = Risk-free rate
  T = Time to expiration
  σ = Volatility
  N() = Cumulative normal distribution
```

### The Greeks
```
Delta (Δ):
  ∂V/∂S
  Call: N(d1), Put: N(d1) - 1
  Hedge ratio

Gamma (Γ):
  ∂²V/∂S²
  Rate of change of delta

Theta (Θ):
  ∂V/∂T
  Time decay (negative for long positions)

Vega (ν):
  ∂V/∂σ
  Sensitivity to volatility

Rho (ρ):
  ∂V/∂r
  Sensitivity to interest rates
```

## 5.3 Hedging Strategies

### Delta Hedging
```
Create delta-neutral position:
  Δ_portfolio = 0

Number of shares to hedge:
  N = -Δ_option × Number of options

Dynamic hedging:
  Continuously adjust as delta changes
```

### Option Strategies
```
Covered Call:
  Long stock + Short call
  Income generation, limited upside

Protective Put:
  Long stock + Long put
  Downside protection

Straddle:
  Long call + Long put (same strike)
  Bet on volatility

Strangle:
  Long OTM call + Long OTM put
  Cheaper volatility bet

Spread:
  Bull spread: Long call, short higher call
  Bear spread: Long put, short lower put

Iron Condor:
  Short strangle + Long strangle (wider)
  Profit from low volatility
```

## 5.4 Other Derivatives

### Forwards and Futures
```
Forward Price:
  F = S × e^(rT)

With dividend yield:
  F = S × e^((r-q)T)

Futures vs Forwards:
  - Futures: Exchange-traded, standardized, margin
  - Forwards: OTC, customized, credit risk
```

### Swaps
```
Interest Rate Swap:
  Exchange fixed for floating payments
  Fixed payer: Pay fixed, receive floating
  Floating payer: Pay floating, receive fixed

Pricing:
  Value of swap = PV(receive leg) - PV(pay leg)
  At initiation: Value = 0

Currency Swap:
  Exchange principal and interest in different currencies
```

---

# 6. PORTFOLIO THEORY

## 6.1 Mean-Variance Optimization

### Portfolio Return and Risk
```
Expected Return:
  E(Rp) = Σ wi × E(Ri)

Portfolio Variance:
  σ²p = Σ Σ wi × wj × σi × σj × ρij
      = w'Σw (matrix notation)

Two-Asset Portfolio:
  σ²p = w₁²σ₁² + w₂²σ₂² + 2w₁w₂σ₁σ₂ρ₁₂
```

### Efficient Frontier
```
Minimize: σ²p = w'Σw
Subject to:
  E(Rp) = w'μ = target return
  Σwi = 1

Lagrangian:
  L = ½w'Σw - λ(w'μ - Rp) - γ(w'1 - 1)

Solution:
  w* = Σ⁻¹[λμ + γ1]
```

### Sharpe Ratio
```
Sharpe Ratio = (Rp - Rf) / σp

Maximum Sharpe:
  Tangency portfolio (market portfolio)

Information Ratio:
  IR = (Rp - Rb) / Tracking Error
  Active return / Active risk
```

## 6.2 Capital Asset Pricing Model

### CAPM Derivation
```
Market Portfolio:
  All risky assets in proportion to market value

Capital Market Line:
  E(Rp) = Rf + [(E(Rm) - Rf)/σm] × σp

Security Market Line:
  E(Ri) = Rf + βi × (E(Rm) - Rf)

Beta:
  βi = Cov(Ri, Rm) / Var(Rm)
     = ρim × (σi/σm)
```

### CAPM Limitations
```
Assumptions violated:
  - Investors not homogeneous
  - No risk-free borrowing/lending
  - Transaction costs exist
  - Taxes affect decisions

Empirical issues:
  - Low-beta stocks outperform CAPM
  - Size and value effects
  - Momentum effect
```

## 6.3 Multi-Factor Models

### Fama-French Three-Factor
```
Ri - Rf = αi + βi(Rm - Rf) + si×SMB + hi×HML + εi

Where:
  SMB = Small Minus Big (size factor)
  HML = High Minus Low (value factor)

Factors explain more variation than CAPM alone
```

### Carhart Four-Factor
```
Add momentum factor (MOM):
  Ri - Rf = αi + βi(Rm-Rf) + si×SMB + hi×HML + mi×MOM + εi

MOM = Return of past winners - past losers
```

### Fama-French Five-Factor
```
Ri - Rf = αi + βi(Rm-Rf) + si×SMB + hi×HML +
          ri×RMW + ci×CMA + εi

Where:
  RMW = Robust Minus Weak (profitability)
  CMA = Conservative Minus Aggressive (investment)
```

## 6.4 Risk Measures

### Value at Risk (VaR)
```
Definition:
  VaR_α = Maximum loss at confidence level α

Calculation Methods:
  Historical: Percentile of historical returns
  Parametric: Assume normal, VaR = -μ + σ × z_α
  Monte Carlo: Simulate scenarios

Example:
  95% VaR of $1M = $50,000
  95% confident loss won't exceed $50,000
```

### Expected Shortfall (CVaR)
```
Average loss when loss exceeds VaR

ES = E[Loss | Loss > VaR]

More coherent risk measure than VaR
Considers tail risk
```

---

# 7. BEHAVIORAL ECONOMICS

## 7.1 Cognitive Biases

### Decision Biases
```
Anchoring:
  Over-rely on first piece of information
  Insufficient adjustment from anchor

Availability Heuristic:
  Judge likelihood by ease of recall
  Recent/vivid events seem more likely

Representativeness:
  Judge probability by similarity
  Ignore base rates

Confirmation Bias:
  Seek information confirming beliefs
  Ignore contradicting evidence
```

### Loss Aversion
```
Prospect Theory:
  Losses loom larger than gains
  Loss aversion coefficient ≈ 2

Value Function:
  - Reference point dependent
  - Concave for gains (risk-averse)
  - Convex for losses (risk-seeking)
  - Steeper for losses

v(x) = x^α for x ≥ 0
v(x) = -λ(-x)^β for x < 0
Where λ ≈ 2.25 (loss aversion)
```

## 7.2 Market Anomalies

### Price Anomalies
```
Momentum:
  Past winners continue winning
  12-month momentum effect

Mean Reversion:
  Long-term reversal
  3-5 year returns reverse

Value Effect:
  High book-to-market outperforms
  Not fully explained by risk

Size Effect:
  Small caps outperform large caps
  January effect concentration
```

### Behavioral Explanations
```
Overconfidence:
  - Trade too much
  - Underestimate risk
  - Overestimate ability

Herding:
  - Follow the crowd
  - Momentum and bubbles

Mental Accounting:
  - Treat money differently by source
  - Disposition effect
```

## 7.3 Nudge Theory

### Choice Architecture
```
Defaults:
  - Default option most likely chosen
  - Opt-in vs opt-out

Framing:
  - How options presented matters
  - Loss vs gain framing

Salience:
  - Visible options more likely
  - Simplify complexity
```

### Applications
```
Retirement Savings:
  - Auto-enrollment increases participation
  - Save More Tomorrow program

Health:
  - Healthy food placement
  - Calorie labeling

Energy:
  - Social comparison on bills
  - Smart defaults
```

---

# 8. GAME THEORY IN BUSINESS

## 8.1 Strategic Games

### Normal Form Games
```
Payoff Matrix (Prisoner's Dilemma):

              Player 2
            Cooperate  Defect
Player 1
Cooperate    (3,3)     (0,5)
Defect       (5,0)     (1,1)

Nash Equilibrium: (Defect, Defect)
Both defect despite mutual cooperation being better
```

### Nash Equilibrium
```
Definition:
  No player can improve by unilaterally changing strategy

Finding Nash:
  1. Find best response for each player
  2. Intersection of best responses

Multiple equilibria possible
Mixed strategy equilibria exist when pure don't
```

## 8.2 Dynamic Games

### Sequential Games
```
Extensive Form:
  - Game tree representation
  - Information sets
  - Subgames

Backward Induction:
  1. Start at terminal nodes
  2. Work backwards
  3. At each node, choose best action

Subgame Perfect Equilibrium:
  Nash equilibrium in every subgame
```

### Repeated Games
```
Finite Repetition:
  - Unraveling argument
  - Same as one-shot at end

Infinite Repetition:
  - Cooperation can be sustained
  - Folk Theorem: Many equilibria

Trigger Strategies:
  - Cooperate until defection
  - Then punish forever (Grim)
  - Or for N periods (Tit-for-tat)
```

## 8.3 Information Economics

### Asymmetric Information
```
Adverse Selection:
  - Hidden information before transaction
  - Market for lemons
  - Solutions: Signaling, screening

Moral Hazard:
  - Hidden action after transaction
  - Principal-agent problem
  - Solutions: Incentives, monitoring
```

### Signaling
```
Spence Job Market Signaling:
  - Education as signal of ability
  - Separating equilibrium
  - High ability gets more education

Conditions for signaling:
  - Signal must be costly
  - Cost lower for high types
  - Receiver believes signal
```

### Mechanism Design
```
Revelation Principle:
  Any mechanism can be replicated by direct mechanism
  where truthful reporting is optimal

Incentive Compatibility:
  Truthful reporting is best strategy

Applications:
  - Auction design
  - Contract theory
  - Public policy
```

## 8.4 Competitive Strategy

### Entry Deterrence
```
Limit Pricing:
  Set price low to signal low costs
  Make entry unprofitable

Capacity Commitment:
  Build excess capacity
  Signal aggressive response to entry

Predatory Pricing:
  Price below cost to drive out competitor
  Recoup losses after exit
  (Often illegal)
```

### Collusion
```
Cartels:
  - Coordinate output/price
  - Maximize joint profits
  - Unstable (cheating incentive)

Facilitating Practices:
  - Price leadership
  - Most-favored-customer clause
  - Meet-the-competition clause
```

---

# 9. MARKET MICROSTRUCTURE

## 9.1 Order Types and Execution

### Order Types
```
Market Order:
  Execute immediately at best available price
  Certainty of execution, uncertain price

Limit Order:
  Execute only at specified price or better
  Uncertain execution, certain price

Stop Order:
  Becomes market order when trigger price reached
  Used for stop-loss or entry

Iceberg Order:
  Large order broken into visible portions
  Hide true size

VWAP Order:
  Execute at volume-weighted average price
  Benchmark execution
```

### Bid-Ask Spread
```
Spread = Ask - Bid

Components:
  - Order processing cost
  - Inventory risk
  - Adverse selection

Quoted Spread: Best ask - Best bid
Effective Spread: 2 × |Trade price - Midpoint|
Realized Spread: 2 × |Trade price - Midpoint_later|
```

## 9.2 Market Making

### Inventory Models
```
Market Maker Problem:
  - Provide liquidity
  - Manage inventory risk
  - Profit from spread

Inventory Risk:
  - Holding unwanted positions
  - Price moves against inventory

Strategies:
  - Adjust quotes based on inventory
  - Hedge positions
  - Limit exposure
```

### Adverse Selection
```
Informed vs Uninformed Traders:
  - Informed: Trade on private information
  - Uninformed: Trade for liquidity

Market Maker Risk:
  - Lose to informed traders
  - Make from uninformed traders

Solutions:
  - Widen spread
  - Reduce quote size
  - Use order flow analysis
```

## 9.3 Price Formation

### Price Discovery
```
Efficient Markets Hypothesis:
  Prices reflect all available information

Forms:
  - Weak: Past prices
  - Semi-strong: Public information
  - Strong: All information

Information Incorporation:
  - Through trading
  - Order flow is informative
```

### Market Impact
```
Temporary Impact:
  - Price deviation during execution
  - Reverts after trade

Permanent Impact:
  - New information incorporated
  - Does not revert

Square Root Law:
  Impact ∝ √(Volume/ADV)
```

## 9.4 High-Frequency Trading

### HFT Strategies
```
Market Making:
  - Provide liquidity
  - Capture spread
  - Manage inventory

Arbitrage:
  - Cross-exchange
  - Statistical arbitrage
  - ETF arbitrage

Directional:
  - Momentum
  - News-based
  - Order flow prediction
```

### Latency
```
Sources of Latency:
  - Network transmission
  - Processing time
  - Exchange matching

Colocation:
  - Place servers near exchange
  - Minimize transmission time

Arms Race:
  - Faster technology
  - Microwave/laser transmission
```

---

# 10. CORPORATE GOVERNANCE INTERNALS

## 10.1 Agency Problems

### Principal-Agent Problem
```
Principals: Shareholders (owners)
Agents: Managers

Conflicts:
  - Effort shirking
  - Empire building
  - Excessive compensation
  - Entrenchment

Costs:
  - Monitoring costs
  - Bonding costs
  - Residual loss
```

### Solutions
```
Incentive Alignment:
  - Equity compensation
  - Performance bonuses
  - Deferred compensation

Monitoring:
  - Board oversight
  - External auditors
  - Activist investors

Market Discipline:
  - Takeover threat
  - Product market competition
  - Managerial labor market
```

## 10.2 Board Structure

### Board Composition
```
Independence:
  - Majority independent directors
  - Separate CEO/Chair
  - Independent committees

Expertise:
  - Industry knowledge
  - Financial literacy
  - Legal/regulatory experience

Diversity:
  - Gender, ethnicity
  - Background, skills
  - Geographic diversity
```

### Committee Functions
```
Audit Committee:
  - Financial reporting oversight
  - Internal controls
  - External auditor relationship

Compensation Committee:
  - Executive pay
  - Incentive plans
  - Pay-performance link

Nominating Committee:
  - Director selection
  - CEO succession
  - Board evaluation
```

## 10.3 Executive Compensation

### Compensation Components
```
Base Salary:
  - Fixed payment
  - Market competitive

Annual Bonus:
  - Performance-based
  - Short-term incentive

Long-term Incentives:
  - Stock options
  - Restricted stock units
  - Performance shares

Benefits/Perks:
  - Retirement plans
  - Insurance
  - Perquisites
```

### Pay-Performance Sensitivity
```
Jensen-Murphy Measure:
  $ change in CEO wealth per $1,000 change in firm value

Option Sensitivity:
  Delta × Number of options × Stock price

Equity Ownership:
  Shares owned × $1,000 / Market cap

Total Sensitivity:
  Sum of all components
```

## 10.4 Shareholder Rights

### Voting Rights
```
Annual Elections:
  - Director elections
  - Auditor ratification
  - Say-on-pay

Special Matters:
  - Charter amendments
  - Mergers/acquisitions
  - Stock issuance

Proxy Voting:
  - Vote by proxy
  - Proxy advisors (ISS, Glass Lewis)
```

### Activism
```
Activist Investors:
  - Acquire stake
  - Push for changes
  - Proxy contests

Common Demands:
  - Board seats
  - Strategic changes
  - Capital allocation
  - Governance improvements

Defense Mechanisms:
  - Poison pills
  - Staggered boards
  - Supermajority requirements
```

---

# 11. M&A MECHANICS

## 11.1 Deal Process

### M&A Process Timeline
```
1. Strategy Development (2-4 weeks)
   - Identify objectives
   - Screen targets

2. Target Approach (2-4 weeks)
   - Initial contact
   - Confidentiality agreement

3. Due Diligence (4-8 weeks)
   - Financial analysis
   - Legal review
   - Operational assessment

4. Negotiation (2-4 weeks)
   - Valuation
   - Deal structure
   - Documentation

5. Signing & Closing (4-12 weeks)
   - Definitive agreement
   - Regulatory approvals
   - Shareholder approval
```

### Due Diligence
```
Financial:
  - Quality of earnings
  - Working capital
  - Debt/commitments
  - Tax

Legal:
  - Contracts
  - Litigation
  - IP
  - Regulatory

Operational:
  - Management
  - Customers
  - Technology
  - HR
```

## 11.2 Deal Structure

### Acquisition Types
```
Stock Purchase:
  - Buy shares from shareholders
  - Assume all liabilities
  - Tax: Seller preference

Asset Purchase:
  - Buy specific assets
  - Choose liabilities
  - Tax: Buyer preference

Merger:
  - Combine entities
  - Requires shareholder approval
  - Tax: Can be tax-free
```

### Consideration
```
Cash:
  - Certainty for sellers
  - Taxable immediately
  - Requires financing

Stock:
  - Shares in acquirer
  - Tax-deferred (if qualified)
  - Shared risk/upside

Mixed:
  - Combination
  - Balance certainty and upside
```

## 11.3 Synergy Analysis

### Types of Synergies
```
Revenue Synergies:
  - Cross-selling
  - Pricing power
  - Market access
  - Higher risk, harder to achieve

Cost Synergies:
  - Headcount reduction
  - Facility consolidation
  - Procurement savings
  - More achievable

Financial Synergies:
  - Tax benefits
  - Debt capacity
  - Lower cost of capital
```

### Synergy Valuation
```
PV of Synergies = Σ [Annual Synergy × (1-T) / (1+r)^t]

Synergy Capture:
  - Buyer vs Seller split
  - Depends on competition
  - Premium paid = Synergy given to seller
```

## 11.4 Accretion/Dilution

### EPS Impact Analysis
```
Accretive: Combined EPS > Acquirer standalone EPS
Dilutive: Combined EPS < Acquirer standalone EPS

Formula:
  Combined EPS = (Acquirer NI + Target NI + Synergies - Financing Cost) /
                 (Acquirer Shares + New Shares Issued)

Breakeven Analysis:
  - P/E at which deal is neutral
  - Synergies needed for accretion
```

---

# 12. PRIVATE EQUITY & VENTURE CAPITAL

## 12.1 PE Fund Structure

### Fund Economics
```
Management Fee:
  - 1.5-2% of committed capital
  - Covers operating expenses

Carried Interest:
  - 20% of profits above hurdle
  - Hurdle: 8% preferred return

Clawback:
  - Return excess carry if later losses
  - True-up at fund end

GP Commitment:
  - 1-5% of fund
  - Alignment with LPs
```

### Fund Life Cycle
```
Fundraising: 6-18 months
Investment Period: 3-5 years
Holding Period: 3-7 years per deal
Harvesting: Years 6-10+
Fund Term: 10-12 years + extensions
```

## 12.2 LBO Mechanics

### LBO Structure
```
Purchase Price = Debt + Equity

Debt Financing:
  - Senior secured: 3-4x EBITDA
  - Second lien: 0.5-1x EBITDA
  - Mezzanine: 1-2x EBITDA
  - Total: 4-6x EBITDA

Equity: 30-50% of purchase price
```

### LBO Returns
```
Sources of Return:
  1. EBITDA growth (operational improvement)
  2. Multiple expansion
  3. Debt paydown

IRR Calculation:
  Exit Value = Exit EBITDA × Exit Multiple
  Equity Value = Exit Value - Remaining Debt
  IRR: Solve for (Equity Value / Initial Equity)^(1/years) - 1

Target Returns:
  IRR: 20-25%+
  Money Multiple: 2-3x
```

## 12.3 Venture Capital

### VC Stages
```
Pre-Seed: < $500K
  - Idea stage
  - Friends, family, angels

Seed: $500K - $2M
  - MVP, early traction
  - Seed funds, angels

Series A: $2M - $15M
  - Product-market fit
  - Scale team, go-to-market

Series B: $15M - $50M
  - Scaling
  - Expand markets, team

Series C+: $50M+
  - Growth, expansion
  - Pre-IPO
```

### VC Term Sheet
```
Economics:
  - Valuation (pre/post-money)
  - Investment amount
  - Option pool

Liquidation Preference:
  - 1x non-participating: Get investment back
  - 1x participating: Investment + pro-rata upside
  - Multiple: 2x, 3x preferences

Anti-dilution:
  - Full ratchet: Adjust to new price
  - Weighted average: Proportional adjustment

Control:
  - Board seats
  - Protective provisions
  - Information rights
```

## 12.4 Exit Strategies

### Exit Options
```
IPO:
  - Highest potential value
  - Long process
  - Market dependent

Strategic Sale:
  - Full liquidity
  - Premium for control
  - Loss of independence

Secondary Sale:
  - Sell to another PE/VC
  - Partial liquidity
  - Company continues

Recapitalization:
  - Dividend recap
  - New debt to pay dividends
  - Partial liquidity
```

---

# 13. TAX STRATEGY

## 13.1 Corporate Tax

### Tax Calculation
```
Taxable Income:
  Revenue
  - Deductible expenses
  - Depreciation/amortization
  = Taxable income

Tax = Taxable Income × Tax Rate

Book vs Tax Differences:
  - Permanent: Never reverse (municipal bond interest)
  - Temporary: Reverse over time (depreciation timing)
```

### Tax Planning
```
Timing:
  - Accelerate deductions
  - Defer income

Entity Selection:
  - Pass-through vs C-corp
  - State tax considerations

Depreciation:
  - Accelerated methods
  - Bonus depreciation
  - Section 179
```

## 13.2 International Tax

### Transfer Pricing
```
Arm's Length Standard:
  Related-party transactions at market prices

Methods:
  - Comparable uncontrolled price
  - Cost plus
  - Resale minus
  - Profit split
  - Transactional net margin

Documentation:
  - Master file
  - Local file
  - Country-by-country reporting
```

### Tax Structures
```
Intellectual Property:
  - Locate IP in low-tax jurisdiction
  - Royalty payments reduce taxable income

Intercompany Financing:
  - Debt vs equity
  - Interest deductions
  - Thin capitalization rules

Supply Chain:
  - Principal structures
  - Limited risk distributors
  - Contract manufacturing
```

## 13.3 M&A Tax

### Deal Structure Tax
```
Taxable vs Tax-Free:
  - Cash deals: Taxable to seller
  - Stock deals: Can be tax-free

338(h)(10) Election:
  - Stock sale treated as asset sale
  - Step-up in basis
  - Tax to seller

Section 368:
  - Tax-free reorganizations
  - Types A, B, C, D, etc.
  - Continuity requirements
```

### Tax Attributes
```
Net Operating Losses (NOLs):
  - Carry forward to offset income
  - Section 382 limitations
  - Ownership change triggers

Tax Credits:
  - R&D credits
  - Investment tax credits
  - May be limited post-acquisition
```

---

# 14. NEGOTIATION SCIENCE

## 14.1 Negotiation Theory

### BATNA
```
Best Alternative To Negotiated Agreement

Importance:
  - Determines walkaway point
  - Source of negotiating power
  - Improve before negotiating

Reservation Price:
  - Minimum acceptable value
  - Walk away if not met

ZOPA:
  Zone of Possible Agreement
  Between reservation prices
```

### Distributive vs Integrative
```
Distributive (Win-Lose):
  - Fixed pie
  - Claim value
  - Competitive

Integrative (Win-Win):
  - Expand pie
  - Create value
  - Collaborative

Most negotiations have elements of both
```

## 14.2 Negotiation Tactics

### Value Creation
```
Interests vs Positions:
  - Understand underlying interests
  - Multiple ways to satisfy

Trade-offs:
  - Different valuations
  - Package deals
  - Logrolling

Information:
  - Share information strategically
  - Ask questions
  - Listen actively
```

### Value Claiming
```
Anchoring:
  - First offer anchors negotiation
  - Aggressive but credible

Concession Strategy:
  - Start high/low
  - Decreasing concessions
  - Reciprocity

Deadlines:
  - Create urgency
  - Real vs artificial
  - Use to your advantage
```

## 14.3 Psychological Factors

### Biases in Negotiation
```
Fixed Pie Assumption:
  - Assume competition
  - Miss integrative solutions

Winner's Curse:
  - Winning bidder overpaid
  - Especially in auctions

Overconfidence:
  - Overestimate BATNA
  - Underestimate other side

Reactive Devaluation:
  - Devalue other side's concessions
  - Because opponent offered it
```

### Building Rapport
```
Active Listening:
  - Paraphrase
  - Ask clarifying questions

Empathy:
  - Understand their perspective
  - Acknowledge concerns

Trust Building:
  - Small agreements first
  - Consistency
  - Transparency
```

---

# 15. ORGANIZATIONAL DESIGN

## 15.1 Structure Design

### Design Parameters
```
Specialization:
  - Horizontal: Division of labor
  - Vertical: Management levels

Coordination:
  - Mutual adjustment: Informal
  - Direct supervision: Manager coordinates
  - Standardization: Rules, outputs, skills

Centralization:
  - Degree of decision authority concentration
  - Centralized vs decentralized
```

### Mintzberg's Configurations
```
Simple Structure:
  - Entrepreneurial
  - Direct supervision
  - Flexible, informal

Machine Bureaucracy:
  - Standardized work
  - Large support staff
  - Efficiency focus

Professional Bureaucracy:
  - Standardized skills
  - Professionals dominate
  - Hospitals, universities

Divisionalized Form:
  - Market-based divisions
  - Standardized outputs
  - Large corporations

Adhocracy:
  - Project teams
  - Mutual adjustment
  - Innovation focus
```

## 15.2 Span of Control

### Factors Affecting Span
```
Wider Span:
  - Routine tasks
  - Experienced employees
  - Similar jobs
  - Good information systems

Narrower Span:
  - Complex tasks
  - New employees
  - Diverse jobs
  - Poor information
```

### Tall vs Flat
```
Tall Organizations:
  - Many levels
  - Narrow spans
  - More control
  - Slower communication

Flat Organizations:
  - Few levels
  - Wide spans
  - Faster decisions
  - Empowerment
```

## 15.3 Modern Structures

### Matrix Organization
```
Dual Reporting:
  - Functional manager
  - Project/product manager

Benefits:
  - Flexibility
  - Expertise sharing
  - Market responsiveness

Challenges:
  - Confusion
  - Conflict
  - Power struggles
```

### Network Organization
```
Hub and Spoke:
  - Core organization
  - Outsourced functions
  - Virtual teams

Benefits:
  - Flexibility
  - Focus on core
  - Access to specialists

Challenges:
  - Coordination
  - Control
  - Dependency
```

---

# 16. INNOVATION MANAGEMENT

## 16.1 Innovation Types

### Innovation Categories
```
Incremental:
  - Improvements to existing
  - Lower risk
  - Sustaining

Radical:
  - New to world
  - Higher risk
  - Breakthrough

Disruptive:
  - Initially inferior
  - Different value network
  - Eventually displaces incumbents

Architectural:
  - New configuration
  - Existing components
  - System-level change
```

### Innovation Domains
```
Product Innovation:
  - New or improved offerings

Process Innovation:
  - New ways of making/delivering

Business Model Innovation:
  - New value creation/capture

Organizational Innovation:
  - New structures, practices
```

## 16.2 Innovation Process

### Stage-Gate Process
```
Stage 0: Discovery
  - Idea generation
  - Gate: Idea screen

Stage 1: Scoping
  - Preliminary investigation
  - Gate: Second screen

Stage 2: Build Business Case
  - Detailed analysis
  - Gate: Go to development

Stage 3: Development
  - Technical development
  - Gate: Go to testing

Stage 4: Testing
  - Market testing
  - Gate: Go to launch

Stage 5: Launch
  - Commercialization
```

### Design Thinking
```
Empathize:
  - Understand users
  - Observe, engage

Define:
  - Problem statement
  - Point of view

Ideate:
  - Generate solutions
  - Brainstorm

Prototype:
  - Build representations
  - Quick, cheap

Test:
  - User feedback
  - Iterate
```

## 16.3 Open Innovation

### Open Innovation Models
```
Outside-In:
  - External ideas, technologies
  - Licensing, acquisition
  - Crowdsourcing

Inside-Out:
  - Exploit internal IP externally
  - Licensing out
  - Spin-offs

Coupled:
  - Combine outside-in and inside-out
  - Joint ventures
  - Alliances
```

### Innovation Ecosystems
```
Components:
  - Startups
  - Universities
  - Research labs
  - Corporate R&D
  - Government
  - Investors

Interactions:
  - Technology transfer
  - Talent flow
  - Capital flow
  - Knowledge sharing
```

---

# 17. BUSINESS MODEL MECHANICS

## 17.1 Business Model Components

### Value Proposition Design
```
Customer Jobs:
  - Functional: Tasks to complete
  - Social: How they want to appear
  - Emotional: How they want to feel

Pains:
  - Undesired outcomes
  - Obstacles
  - Risks

Gains:
  - Desired outcomes
  - Benefits expected
  - Surprises that delight

Value Map:
  - Pain relievers
  - Gain creators
  - Products/services
```

### Revenue Model Patterns
```
Transaction:
  - One-time payment
  - Product sales, fees

Recurring:
  - Subscription
  - Usage-based
  - Licensing

Hybrid:
  - Freemium
  - Razor/blade
  - Platform fees
```

## 17.2 Business Model Patterns

### Platform Patterns
```
Marketplace:
  - Connect buyers and sellers
  - Transaction fees
  - Examples: eBay, Airbnb

Aggregator:
  - Curate offerings
  - Own customer relationship
  - Examples: Amazon, Netflix

Social Network:
  - User-generated content
  - Ad-supported
  - Examples: Facebook, TikTok
```

### Non-Platform Patterns
```
Direct-to-Consumer:
  - Own the channel
  - Higher margins
  - Customer relationship

As-a-Service:
  - Product to service
  - Recurring revenue
  - Lower upfront cost

Franchise:
  - License business model
  - Fee + royalties
  - Scalability
```

## 17.3 Business Model Innovation

### Disruption Patterns
```
Low-End Disruption:
  - Target overserved customers
  - Simpler, cheaper
  - Good enough quality

New-Market Disruption:
  - Non-consumers
  - Create new market
  - Different value network

Platform Disruption:
  - Network effects
  - Disintermediation
  - Winner-take-most
```

### Model Validation
```
Key Assumptions:
  - Customer exists
  - Problem is important
  - Solution works
  - They will pay
  - Profitable unit economics

Testing:
  - Customer interviews
  - MVPs
  - Pilot programs
  - A/B tests
```

---

# 18. NETWORK EFFECTS & PLATFORM ECONOMICS

## 18.1 Network Effect Types

### Direct Network Effects
```
Same-side:
  Value = f(N^a), a > 0

Metcalfe's Law:
  V ∝ N² (all possible connections)

Reed's Law:
  V ∝ 2^N (group forming networks)

Examples:
  - Phone network
  - Social networks
  - Communication apps
```

### Indirect Network Effects
```
Cross-side:
  More users → More complements → More users

Two-Sided Market:
  - Buyers value sellers
  - Sellers value buyers

Examples:
  - Operating systems (users/developers)
  - Marketplaces (buyers/sellers)
  - Payment cards (merchants/cardholders)
```

## 18.2 Platform Dynamics

### Chicken-and-Egg Problem
```
Need both sides to have any side

Strategies:
  - Subsidize one side
  - Single-player mode
  - Seed with content
  - Fake it until make it
  - Piggybacking
```

### Winner-Take-Most
```
Conditions:
  - Strong network effects
  - Low multi-homing
  - Limited differentiation

Not Absolute:
  - Multiple equilibria possible
  - Differentiation possible
  - Niche markets
```

## 18.3 Platform Strategy

### Pricing Strategy
```
Subsidize elastic side:
  - Price low on price-sensitive side
  - Charge more on inelastic side

Freemium:
  - Free basic tier
  - Monetize power users

Transaction fees:
  - Percentage of GMV
  - Flat per-transaction
```

### Growth Strategy
```
User Acquisition:
  - Viral mechanics
  - Referral programs
  - Content marketing

Engagement:
  - Reduce friction
  - Increase frequency
  - Build habits

Retention:
  - Switching costs
  - Data lock-in
  - Community
```

---

# 19. PRICING SCIENCE

## 19.1 Pricing Fundamentals

### Cost-Based Pricing
```
Cost-Plus:
  Price = Cost × (1 + Markup%)

Target Return:
  Price = Unit Cost + (Target Return × Investment) / Expected Sales

Problems:
  - Ignores demand
  - Ignores competition
  - Ignores value
```

### Value-Based Pricing
```
Economic Value to Customer (EVC):
  Reference value + Differentiation value

Reference Value:
  - Next best alternative price

Differentiation Value:
  - Benefits above reference
  - Quantified in $ terms

Price = % of EVC captured
```

## 19.2 Price Optimization

### Price Elasticity
```
Own-Price Elasticity:
  ε = (∂Q/∂P) × (P/Q)

Optimal Markup:
  (P - MC) / P = 1 / |ε|

Higher elasticity → Lower markup
Lower elasticity → Higher markup
```

### Price Discrimination
```
First Degree:
  - Individual prices
  - Capture all consumer surplus
  - Rare (auctions approximate)

Second Degree:
  - Self-selection
  - Quantity discounts
  - Versioning

Third Degree:
  - Segment-based
  - Different prices by group
  - Student, senior discounts
```

## 19.3 Dynamic Pricing

### Revenue Management
```
Applications:
  - Airlines
  - Hotels
  - Events
  - Ride-sharing

Principles:
  - Fixed capacity
  - Perishable inventory
  - Variable demand
  - Segment customers
```

### Algorithmic Pricing
```
Approaches:
  - Rule-based
  - Demand forecasting
  - Reinforcement learning
  - Competitive monitoring

Considerations:
  - Price wars
  - Customer perception
  - Legal issues
```

## 19.4 Behavioral Pricing

### Reference Prices
```
Internal Reference:
  - Memory of past prices
  - Expectations

External Reference:
  - Competitor prices
  - List/sale prices

Loss Aversion:
  - Price increases hurt more than decreases help
  - Frame as discount vs surcharge
```

### Price Framing
```
Anchoring:
  - Show high price first
  - Compare to expensive alternative

Partitioned Pricing:
  - Separate base and fees
  - Lower perceived price

Decoy Effect:
  - Add dominated option
  - Make target more attractive
```

---

# 20. DECISION THEORY

## 20.1 Decision Framework

### Decision Elements
```
Alternatives: Options available
States: Uncertain future events
Outcomes: Results of alternative × state
Probabilities: Likelihood of states
Values: Preference for outcomes
```

### Decision Criteria
```
Expected Value:
  EV = Σ p_i × v_i

Maximax:
  Choose highest possible outcome
  Risk-seeking

Maximin:
  Choose highest minimum outcome
  Risk-averse

Minimax Regret:
  Minimize maximum regret
```

## 20.2 Expected Utility Theory

### Utility Functions
```
Expected Utility:
  EU = Σ p_i × u(x_i)

Risk Attitudes:
  - Risk-averse: u''(x) < 0 (concave)
  - Risk-neutral: u''(x) = 0 (linear)
  - Risk-seeking: u''(x) > 0 (convex)

Common Functions:
  - Log: u(x) = ln(x)
  - Power: u(x) = x^α, 0 < α < 1
  - Exponential: u(x) = 1 - e^(-ax)
```

### Certainty Equivalent
```
CE: Certain amount equivalent to gamble

u(CE) = EU(gamble)

Risk Premium:
  RP = EV - CE

Higher risk aversion → Higher RP
```

## 20.3 Bayesian Decision Making

### Bayes' Theorem
```
P(H|E) = P(E|H) × P(H) / P(E)

Where:
  P(H|E) = Posterior (after evidence)
  P(H) = Prior (before evidence)
  P(E|H) = Likelihood
  P(E) = Marginal likelihood
```

### Value of Information
```
Expected Value of Perfect Information (EVPI):
  EVPI = EV with perfect info - EV without

Expected Value of Sample Information (EVSI):
  EVSI = EV with sample info - EV without

Efficiency:
  EVSI / EVPI
```

## 20.4 Multi-Criteria Decision Making

### Weighted Scoring
```
Score = Σ w_i × s_i

Where:
  w_i = Weight of criterion i
  s_i = Score on criterion i
  Σ w_i = 1
```

### Analytic Hierarchy Process (AHP)
```
Steps:
1. Structure hierarchy
2. Pairwise comparisons
3. Calculate priorities
4. Check consistency
5. Synthesize

Consistency Ratio:
  CR = CI / RI
  Should be < 0.1
```

### MCDA Techniques
```
TOPSIS:
  - Distance from ideal solution
  - Closest to positive, farthest from negative

ELECTRE:
  - Outranking method
  - Concordance and discordance

PROMETHEE:
  - Preference functions
  - Net flow ranking
```

---

# SUMMARY

This advanced document covers the deep internals of business:

1. **Economics**: Micro/macro theory, models, growth
2. **Finance**: Valuation math, derivatives, portfolio theory
3. **Behavior**: Biases, game theory, decision theory
4. **Markets**: Microstructure, M&A, PE/VC
5. **Strategy**: Governance, negotiation, pricing
6. **Organizations**: Design, innovation, platforms

Each section provides the mathematical foundations and strategic frameworks that drive business decisions.

---

*Last Updated: 2024*
*Coverage: Deep Business Internals*
