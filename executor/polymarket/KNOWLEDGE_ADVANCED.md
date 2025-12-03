# Polymarket Advanced Knowledge Base

## Deep Technical Details

### Conditional Tokens Framework (CTF)

#### Token ID Calculation
```
Condition ID = keccak256(
  abi.encodePacked(oracle, questionId, outcomeSlotCount)
)

Collection ID = keccak256(
  abi.encodePacked(conditionId, indexSet)
)

Position ID (ERC-1155 token ID) = uint256(keccak256(
  abi.encodePacked(collateralToken, collectionId)
))
```

#### Index Sets
```
Binary Markets:
- YES outcome: indexSet = 1 (binary: 01)
- NO outcome: indexSet = 2 (binary: 10)

Multi-Outcome (4 outcomes):
- Outcome A: indexSet = 1 (binary: 0001)
- Outcome B: indexSet = 2 (binary: 0010)
- Outcome C: indexSet = 4 (binary: 0100)
- Outcome D: indexSet = 8 (binary: 1000)

Combined Positions:
- A or B: indexSet = 3 (binary: 0011)
- Not D: indexSet = 7 (binary: 0111)
```

#### Partition Constraints
```
For valid market:
- Outcomes must be mutually exclusive
- Outcomes must be collectively exhaustive
- Index sets must form complete partition
- Sum of all outcome probabilities = 1
```

### Order Signing Deep Dive

#### EIP-712 Domain Separator
```solidity
bytes32 DOMAIN_SEPARATOR = keccak256(
    abi.encode(
        keccak256("EIP712Domain(string name,string version,uint256 chainId)"),
        keccak256("Polymarket CTF Exchange"),
        keccak256("1"),
        137  // Polygon chainId
    )
);
```

#### Order Hash Calculation
```solidity
bytes32 orderHash = keccak256(
    abi.encodePacked(
        "\x19\x01",
        DOMAIN_SEPARATOR,
        keccak256(abi.encode(
            ORDER_TYPEHASH,
            order.salt,
            order.maker,
            order.signer,
            order.taker,
            order.tokenId,
            order.makerAmount,
            order.takerAmount,
            order.expiration,
            order.nonce,
            order.feeRateBps,
            order.side,
            order.signatureType
        ))
    )
);
```

#### Signature Types Explained
```
Type 0 - EOA:
- Standard ECDSA signature
- r, s, v components
- 65 bytes total

Type 1 - EIP-1271 (Contract):
- Smart contract signature
- Contract implements isValidSignature()
- Used by Poly Proxy wallets

Type 2 - Poly Gnosis Safe:
- Multi-signature support
- Threshold of signers required
- EIP-1271 compliant
```

### Nonce Management
```
Global Nonce:
- Per-address incrementing counter
- Used for order uniqueness
- Cannot reuse nonces

Salt vs Nonce:
- Salt: Random, for order uniqueness
- Nonce: Global, for replay protection
- Both must be unique per order
```

---

## Order Matching Engine Details

### Matching Algorithm
```
1. ORDER ARRIVAL
   - Validate signature
   - Check balances/allowances
   - Verify price/size constraints

2. BOOK LOOKUP
   - Find matching orders on opposite side
   - Price-time priority sorting

3. MATCHING LOOP
   For each potential match:
   - Calculate fill amount
   - Check self-trade prevention
   - Verify remaining balances
   - Create fill record

4. SETTLEMENT BATCH
   - Aggregate fills into settlement batch
   - Submit to on-chain contract
   - Emit events
```

### Price-Time Priority
```
Example Order Book (Bids):
Time    Price   Size    Priority
10:01   $0.65   100     1 (best price)
10:00   $0.64   200     2 (earlier time)
10:02   $0.64   150     3 (later time)
10:03   $0.63   300     4 (worse price)

Incoming Sell at $0.64:
- First fills against $0.65 bid (100 shares)
- Then fills against $0.64 bid from 10:00 (200 shares)
- Then fills against $0.64 bid from 10:02 (150 shares)
```

### Self-Trade Prevention (STP)
```
Modes:
- CANCEL_NEWEST: Cancel incoming order
- CANCEL_OLDEST: Cancel resting order
- CANCEL_BOTH: Cancel both orders
- DECREMENT: Reduce size of both

Polymarket Default: CANCEL_NEWEST
- Incoming order cancelled if would self-trade
- Resting order preserved
```

### Partial Fill Handling
```
Scenario: Buy 1000 @ $0.65, only 400 available

Result:
- Fill: 400 @ $0.65
- Resting: 600 @ $0.65 (remains on book for GTC)
- Or: Cancel remainder (for IOC)
- Or: Cancel entire (for FOK)
```

---

## Resolution Mechanics Deep Dive

### UMA Optimistic Oracle Protocol

#### Data Request Flow
```
1. REQUEST INITIALIZATION
   - Market creator specifies:
     - ancillaryData (resolution criteria)
     - customLiveness (challenge period)
     - bondAmount

2. PRICE PROPOSAL
   - Anyone can propose resolution
   - Must stake bond
   - Asserts: "YES wins" or "NO wins"

3. DISPUTE PERIOD
   - 2 hours for standard markets
   - Anyone can dispute by staking bond
   - No dispute = proposal accepted

4. DVM VOTE (if disputed)
   - UMA token holders vote
   - 48-96 hour voting period
   - Majority determines outcome
   - Winner gets bonds, loser loses
```

#### Ancillary Data Format
```
Example:
"q: Will Bitcoin exceed $100,000 by December 31, 2024, 11:59 PM ET?
res_data: p1: 0, p2: 1, p3: 0.5
Where p1 corresponds to NO, p2 to YES, p3 to unknown/ambiguous."

Components:
- q: Question text
- res_data: Resolution values
- p1: NO value (usually 0)
- p2: YES value (usually 1)
- p3: Ambiguous value (usually 0.5)
```

#### Edge Case Resolutions

**Market Voiding**
```
When:
- Event cancelled (game postponed indefinitely)
- Ambiguous criteria
- Resolution source unavailable
- Force majeure

Result:
- All tokens worth $0.50 (or original price)
- Or full refund of collateral
- Determined by market rules
```

**Partial Resolution**
```
When:
- Outcome falls between YES/NO
- Multiple interpretations valid

Example:
- "Company announces product by Q4"
- Announced December 31, ambiguous timezone
- May resolve to 0.5 (50/50)
```

**Multi-Part Events**
```
When:
- Market has compound criteria
- Some parts true, some false

Resolution:
- Usually follows most specific rule
- May require UMA vote
- Check ancillary data carefully
```

---

## Market Microstructure

### Spread Dynamics

#### Factors Affecting Spread
```
1. INFORMATION ASYMMETRY
   - Higher expected info → wider spread
   - Breaking news → spread widens

2. INVENTORY RISK
   - Market makers adjust for position
   - Long inventory → lower bids
   - Short inventory → higher asks

3. COMPETITION
   - More market makers → tighter spreads
   - Monopolistic MM → wider spreads

4. TIME TO RESOLUTION
   - Near expiry → tighter spreads
   - Far expiry → wider spreads

5. VOLATILITY
   - High vol → wider spreads
   - Low vol → tighter spreads
```

#### Spread Calculation Methods
```
Quoted Spread:
spread = best_ask - best_bid

Relative Spread:
relative = spread / mid_price

Effective Spread:
effective = 2 × |execution_price - mid_price|

Realized Spread:
realized = 2 × (execution_price - mid_5min_later)
```

### Market Impact Models

#### Square Root Model
```
Impact = σ × sqrt(Q/V)

Where:
- σ = volatility
- Q = order size
- V = daily volume

Example:
- σ = 0.05 (5% daily vol)
- Q = 1000 shares
- V = 10000 daily volume
- Impact = 0.05 × sqrt(0.1) = 1.58%
```

#### Linear Model
```
Impact = λ × Q

Where:
- λ = market impact coefficient
- Q = order size

Typical λ: 0.0001 to 0.001 per share
```

#### Kyle's Lambda
```
From Kyle (1985):
λ = σ / sqrt(V × depth)

Measures price impact per unit of order flow
Higher λ = less liquid market
```

### Order Flow Analysis

#### Buy/Sell Imbalance
```
OFI = (Buy Volume - Sell Volume) / Total Volume

Interpretation:
- OFI > 0.2: Strong buy pressure
- OFI < -0.2: Strong sell pressure
- -0.2 < OFI < 0.2: Balanced
```

#### Trade Arrival Rate (Poisson)
```
λ = number of trades / time period

Expected trades in interval t:
E[N(t)] = λ × t

Variance:
Var[N(t)] = λ × t
```

---

## Advanced Trading Concepts

### Kelly Criterion Variations

#### Full Kelly
```
f* = (p × b - q) / b

Where:
- f* = fraction to bet
- p = probability of winning
- b = decimal odds - 1
- q = 1 - p

Example:
- p = 0.6, price = $0.50
- b = 1/0.5 - 1 = 1
- f* = (0.6 × 1 - 0.4) / 1 = 0.2
- Bet 20% of bankroll
```

#### Fractional Kelly
```
Half Kelly: f*/2 (most common)
Quarter Kelly: f*/4 (conservative)

Why Fractional:
- Accounts for estimation error
- Reduces variance
- Avoids ruin from overestimation
```

#### Kelly with Multiple Bets
```
For correlated bets:
f_i = (Σ_j C^(-1)_ij × μ_j) / wealth

Where:
- C = covariance matrix
- μ = expected returns vector
- Requires portfolio optimization
```

### Arbitrage Mathematics

#### Binary Arbitrage
```
Condition: YES + NO < 1 (underpriced)

Profit Calculation:
- Buy YES @ p_y, Buy NO @ p_n
- Total cost: p_y + p_n < 1
- Guaranteed return: $1
- Profit: 1 - (p_y + p_n)

Example:
- YES @ $0.55, NO @ $0.43
- Cost: $0.98
- Profit: $0.02 per $0.98 = 2.04% risk-free
```

#### Cross-Market Arbitrage
```
Same Event, Different Platforms:
- Platform A: YES @ $0.60
- Platform B: YES @ $0.55

Strategy:
- Buy YES on B @ $0.55
- Sell YES on A @ $0.60 (if possible)
- Or: Buy NO on A @ $0.40

Risks:
- Settlement timing differences
- Platform risk
- Execution slippage
```

#### Triangular Arbitrage (Multi-Outcome)
```
For 3-outcome market A, B, C:
If: p_A + p_B + p_C < 1

Buy all three:
- Cost: p_A + p_B + p_C
- Return: $1 (one wins)
- Profit: 1 - (p_A + p_B + p_C)
```

### Probability Calibration

#### Brier Score
```
BS = (1/N) × Σ(f_t - o_t)²

Where:
- f_t = forecast probability
- o_t = actual outcome (0 or 1)
- N = number of forecasts

Interpretation:
- BS = 0: Perfect
- BS = 0.25: Random (for binary)
- BS < 0.25: Better than random
```

#### Calibration Curve
```
For each probability bucket [0.1, 0.2):
- Count predictions in bucket
- Calculate actual outcome rate
- Plot predicted vs actual

Well-Calibrated:
- Points lie on 45° line
- 70% predictions true 70% of time

Overconfident:
- Points below line (high probabilities)
- Points above line (low probabilities)
```

#### Log Loss
```
LL = -(1/N) × Σ[o_t × log(f_t) + (1-o_t) × log(1-f_t)]

Properties:
- Heavily penalizes confident wrong predictions
- Used in ML model evaluation
- Lower is better
```

---

## Market Making Theory

### Avellaneda-Stoikov Model
```
Optimal Bid: S - reservation_spread/2 - skew
Optimal Ask: S + reservation_spread/2 - skew

reservation_spread = γ × σ² × T
skew = γ × σ² × q × T

Where:
- S = mid price
- γ = risk aversion
- σ = volatility
- T = time horizon
- q = inventory
```

### Inventory Management

#### Symmetric Inventory
```
Target: q = 0 (flat)
Method: Adjust quotes to attract balancing flow

When long (q > 0):
- Lower bid price
- Lower ask price
- Attracts sellers

When short (q < 0):
- Raise bid price
- Raise ask price
- Attracts buyers
```

#### Asymmetric Quoting
```
When q > threshold:
- Only quote asks (sell to reduce)
- Widen bid (discourage buys)

When q < -threshold:
- Only quote bids (buy to cover)
- Widen ask (discourage sells)
```

### Adverse Selection
```
Problem:
- Informed traders trade against you
- Always on wrong side with informed

Detection:
- Monitor realized spread
- Track post-trade price movement
- Identify toxic flow patterns

Defense:
- Widen spreads during news
- Reduce size during high volatility
- Cancel quotes on large orders
```

---

## Network and Infrastructure

### Polygon Network Details
```
Block Time: ~2 seconds
Finality: ~2-3 blocks (4-6 seconds)
Gas Costs: ~0.01-0.1 MATIC per transaction
RPC Endpoints:
- https://polygon-rpc.com
- https://rpc-mainnet.matic.network
- Alchemy, Infura, QuickNode
```

### Settlement Batching
```
Polymarket batches settlements:
- Multiple fills aggregated
- Single on-chain transaction
- Reduces gas costs
- Slight delay from match to settle

Typical Batch:
- Every few seconds
- Or on trade threshold
- Or force settle on demand
```

### Websocket Message Types
```
Order Book Snapshot:
{
  "type": "book_snapshot",
  "asset_id": "...",
  "bids": [[price, size], ...],
  "asks": [[price, size], ...],
  "timestamp": 1234567890
}

Order Book Delta:
{
  "type": "book_update",
  "asset_id": "...",
  "changes": {
    "bids": [[price, size], ...],
    "asks": [[price, size], ...]
  }
}

Trade:
{
  "type": "trade",
  "asset_id": "...",
  "price": "0.65",
  "size": "100",
  "side": "BUY",
  "timestamp": 1234567890
}
```

---

## Edge Cases and Gotchas

### Common Pitfalls

#### Price Precision
```
Problem: Floating point errors
Wrong: 0.1 + 0.2 = 0.30000000000000004

Solution: Use fixed-point arithmetic
- Multiply by 1000 (tick size)
- Work in integers
- Divide at end
```

#### Timing Issues
```
Problem: Order expires during submission

Solution:
- Add buffer to expiration
- GTD expiration = now + duration + buffer
- Handle expired order responses
```

#### Balance Race Conditions
```
Problem: Multiple orders exceed balance

Scenario:
- Balance: $100
- Order 1: Buy 200 @ $0.50 = $100
- Order 2: Buy 200 @ $0.50 = $100
- Both submitted simultaneously

Result: One or both may fail

Solution:
- Track pending order value
- Reserve balance for pending
- Sequential order submission
```

### API Quirks

#### Empty Responses
```
GET /orders may return:
- [] if no orders
- {"orders": []}
- null (check for this)

Always handle:
response.get('orders', []) or []
```

#### Timestamp Formats
```
API uses multiple formats:
- Unix timestamp (seconds): 1234567890
- Unix timestamp (ms): 1234567890000
- ISO 8601: "2024-01-01T00:00:00Z"

Always verify which format expected
```

#### Order ID Types
```
- Some endpoints: string
- Some endpoints: integer
- Always cast to string for safety
```

### Resolution Edge Cases

#### Time Zone Ambiguity
```
Market: "Will X happen by December 31, 2024?"

Questions:
- Which timezone?
- End of day = midnight or 11:59 PM?
- Server time or event location time?

Resolution: Check ancillary data
Usually: UTC or specified timezone
```

#### Definition Disputes
```
Market: "Will company announce product?"

Ambiguities:
- What counts as "announce"?
- Tweet? Press release? Earnings call?
- Prototype or production ready?

Resolution: UMA vote on interpretation
```

---

## Performance Optimization

### Order Submission Latency
```
Typical Latencies:
- API request: 50-200ms
- WebSocket update: 10-50ms
- On-chain settlement: 2-6 seconds

Optimization:
- Co-locate near API servers
- Persistent connections
- Pre-sign orders
- Batch similar orders
```

### Data Management
```
Order Book:
- Full snapshot: ~100KB
- Delta updates: ~1KB
- Rebuild from deltas
- Periodic full refresh

Trade History:
- Paginate requests
- Cache locally
- Incremental updates
```

### Resource Usage
```
WebSocket Connections:
- Limit: 1 per API key
- Reconnect on disconnect
- Heartbeat to maintain

Memory:
- Order book per market: ~1MB
- Trade history: grows unbounded
- Implement rolling window
```

---

## Tax and Compliance

### Record Keeping Requirements
```
For Each Trade:
- Date and time
- Market identifier
- Side (buy/sell)
- Price
- Size
- Fees paid
- Position after trade

For Each Resolution:
- Market outcome
- Payout received
- Cost basis
- Profit/loss
```

### Tax Treatment (Varies by Jurisdiction)
```
Common Classifications:
- Capital gains (most jurisdictions)
- Gambling winnings (some)
- Ordinary income (some)

Considerations:
- Short-term vs long-term holding
- Wash sale rules
- Loss harvesting opportunities
```

### AML Considerations
```
Polymarket Requirements:
- KYC for large withdrawals
- Source of funds verification
- Transaction monitoring

User Responsibilities:
- Comply with local laws
- Report income accurately
- Maintain records
```

---

*This document contains advanced technical details for sophisticated traders and developers. Always verify current platform specifications as they may change.*
