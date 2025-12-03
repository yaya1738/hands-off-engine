# Polymarket Complete Knowledge Base

## Table of Contents
1. [Platform Overview](#platform-overview)
2. [Technical Architecture](#technical-architecture)
3. [Market Structure](#market-structure)
4. [Trading Mechanics](#trading-mechanics)
5. [Order Book (CLOB)](#order-book-clob)
6. [Resolution System](#resolution-system)
7. [Fee Structure](#fee-structure)
8. [Smart Contracts](#smart-contracts)
9. [API Reference](#api-reference)
10. [Wallet & Signatures](#wallet--signatures)
11. [Market Categories](#market-categories)
12. [Liquidity Dynamics](#liquidity-dynamics)
13. [Risk Factors](#risk-factors)
14. [Regulatory Context](#regulatory-context)
15. [Historical Evolution](#historical-evolution)
16. [Trading Patterns](#trading-patterns)
17. [Best Practices](#best-practices)

---

## Platform Overview

### What is Polymarket?
Polymarket is a decentralized prediction market platform where users trade on the outcomes of real-world events. Unlike traditional betting, Polymarket uses blockchain technology (Polygon) to enable peer-to-peer trading of outcome shares.

### Key Characteristics
- **Decentralized**: No central bookmaker; users trade against each other
- **Non-custodial**: Users control their own funds via wallets
- **Transparent**: All trades and positions visible on-chain
- **Global**: Accessible worldwide (with some jurisdictional restrictions)
- **24/7**: Markets trade continuously until resolution

### Founding & History
- Founded: 2020 by Shayne Coplan
- Initial focus: US election markets
- Regulatory challenges: 2022 CFTC settlement ($1.4M fine)
- Growth: Became largest prediction market by volume (2024)
- Peak volume: Billions in trading volume during 2024 US election

### Core Value Proposition
- **Price Discovery**: Market prices aggregate collective wisdom
- **Information Efficiency**: Prices react quickly to new information
- **Hedging**: Users can hedge real-world event risk
- **Speculation**: Trade on beliefs about future outcomes

---

## Technical Architecture

### Blockchain Layer
```
Network: Polygon (formerly Matic)
Chain ID: 137
Block Time: ~2 seconds
Consensus: Proof of Stake
Gas Token: MATIC (users don't pay gas directly)
```

### Collateral
```
Token: USDC (USD Coin)
Contract: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 (Polygon)
Decimals: 6
Standard: ERC-20
```

### Key Infrastructure Components
1. **CLOB (Central Limit Order Book)**: Off-chain order matching
2. **CTF Exchange**: On-chain settlement contract
3. **Conditional Tokens**: ERC-1155 outcome tokens
4. **UMA Oracle**: Decentralized resolution system
5. **Gnosis Conditional Tokens Framework**: Token standard

### Architecture Flow
```
User Wallet → CLOB API → Order Matching (off-chain) → CTF Exchange (on-chain)
                                                            ↓
                                                   Conditional Tokens
                                                            ↓
                                                   Resolution (UMA)
                                                            ↓
                                                   Redemption
```

### Hybrid Model
- **Off-chain**: Order submission, matching, cancellation
- **On-chain**: Settlement, token transfers, resolution
- Benefits: Low latency, no gas for orders, on-chain security for settlement

---

## Market Structure

### Binary Markets
The most common market type on Polymarket.

```
Structure:
- Two outcomes: YES and NO
- Each outcome is a separate token
- Constraint: YES price + NO price ≈ $1.00
- Resolution: One outcome pays $1.00, other pays $0.00

Example:
"Will Bitcoin reach $100k by Dec 31, 2024?"
- YES token: Currently $0.65
- NO token: Currently $0.35
- If BTC reaches $100k: YES → $1.00, NO → $0.00
- If BTC doesn't: YES → $0.00, NO → $1.00
```

### Multi-Outcome Markets
Markets with more than two mutually exclusive outcomes.

```
Structure:
- N outcomes (typically 3-10)
- All outcome tokens sum to $1.00
- Only one outcome can win
- Winner pays $1.00, others pay $0.00

Example:
"Who will win the 2024 Presidential Election?"
- Trump: $0.52
- Harris: $0.46
- Other: $0.02
Total: $1.00
```

### Scalar Markets (Rare)
Markets resolving to a numeric value within a range.

```
Structure:
- Continuous range of outcomes
- Payout proportional to final value
- Less common on Polymarket

Example:
"What will be the S&P 500 close on Dec 31?"
- Range: 4000-6000
- If closes at 5000: Payout at 50% of range
```

### Market Lifecycle
```
1. CREATION
   - Market proposed and approved
   - Initial liquidity provided
   - Trading begins

2. ACTIVE
   - Open for trading
   - Prices fluctuate based on supply/demand
   - Can last days to years

3. CLOSED
   - Trading ends (usually at event time)
   - No new orders accepted
   - Awaiting resolution

4. RESOLUTION
   - Outcome determined via UMA oracle
   - 2-hour challenge period
   - Can be disputed

5. SETTLED
   - Final outcome confirmed
   - Winning tokens redeemable for $1.00
   - Losing tokens worth $0.00

6. REDEMPTION
   - Users claim winnings
   - Tokens burned for USDC
   - Market complete
```

---

## Trading Mechanics

### Price Interpretation
```
Price = Implied Probability
- $0.65 YES = 65% implied probability of YES
- $0.35 NO = 35% implied probability of NO

Decimal Odds = 1 / Price
- $0.65 → 1.54x return if correct
- $0.35 → 2.86x return if correct
```

### Order Types

#### Good Till Cancelled (GTC)
```
- Default order type
- Remains on book until filled or cancelled
- No expiration
- Best for: Passive trading, market making
```

#### Good Till Date (GTD)
```
- Expires at specified timestamp
- Auto-cancels at expiration
- Best for: Time-sensitive strategies
- Requires: expiration parameter (Unix timestamp)
```

#### Fill Or Kill (FOK)
```
- Must fill entirely or cancel completely
- No partial fills allowed
- Immediate execution or nothing
- Best for: Large orders requiring atomicity
```

#### Immediate Or Cancel (IOC)
```
- Fill what's available, cancel rest
- Accepts partial fills
- No resting on book
- Best for: Taking liquidity quickly
```

### Order Constraints
```
Minimum Price: $0.001 (0.1%)
Maximum Price: $0.999 (99.9%)
Tick Size: $0.001
Minimum Order: $0.01
Maximum Order: $100,000 (soft limit)
Price Precision: 3 decimal places
Size Precision: 2 decimal places
```

### Position Limits
```
No hard position limits per user
Soft limits may apply for large positions
Market makers may have higher limits
Liquidity determines practical limits
```

### Trading Hours
```
24/7/365 trading
No market hours or closures
Markets close only at resolution time
```

---

## Order Book (CLOB)

### Central Limit Order Book
Polymarket uses an off-chain CLOB for order matching with on-chain settlement.

### Order Book Structure
```
BIDS (Buy Orders)          ASKS (Sell Orders)
Price    Size              Price    Size
$0.64    500               $0.66    300
$0.63    1,200             $0.67    800
$0.62    2,500             $0.68    1,500
$0.61    800               $0.69    400
$0.60    3,000             $0.70    2,000

Spread = Best Ask - Best Bid = $0.66 - $0.64 = $0.02
Mid Price = ($0.64 + $0.66) / 2 = $0.65
```

### Matching Rules
```
1. Price-Time Priority
   - Best price matched first
   - At same price, earlier orders matched first

2. Maker/Taker
   - Maker: Adds liquidity (limit order on book)
   - Taker: Removes liquidity (crosses spread)

3. Self-Trade Prevention
   - Orders cannot match against same user's orders
   - Self-trades are prevented at matching engine
```

### Order States
```
LIVE: Active on order book
MATCHED: Fully filled
CANCELLED: User cancelled
EXPIRED: GTD order expired
PARTIALLY_FILLED: Some fills, remainder on book
```

### Rate Limits
```
API Requests: 100 per 10 seconds per IP
Order Submissions: 10 per second per address
WebSocket: 1 connection per API key
```

---

## Resolution System

### UMA Optimistic Oracle
Polymarket uses UMA's Optimistic Oracle for decentralized resolution.

### How UMA Works
```
1. ASSERTION
   - Anyone can assert an outcome
   - Must post bond (starting ~$750 USDC)
   - Assertion includes resolution data

2. CHALLENGE PERIOD
   - 2-hour window for disputes
   - If no dispute: assertion accepted
   - If disputed: goes to UMA DVM

3. DISPUTE RESOLUTION
   - UMA token holders vote
   - Correct party gets bond back + reward
   - Incorrect party loses bond

4. FINAL RESOLUTION
   - Outcome confirmed on-chain
   - Tokens become redeemable
```

### Bond Structure
```
Initial Bond: ~$750 USDC
Each Dispute Level: Bond doubles
Level 0: $750
Level 1: $1,500
Level 2: $3,000
Level 3: $6,000
...continues doubling
```

### Resolution Sources
Markets specify authoritative sources for resolution:
```
- Official government sources
- Major news organizations (AP, Reuters)
- Sports leagues (NFL, NBA official results)
- Cryptocurrency price feeds (Chainlink, CoinGecko)
- Company announcements
- Academic/scientific publications
```

### Edge Cases
```
AMBIGUOUS: Market may resolve to partial value or void
CANCELLED: Event cancelled, market voided, refunds issued
DISPUTED: Extended timeline while dispute resolves
EARLY RESOLUTION: Market may close early if outcome known
```

### Resolution Timeline
```
Typical Timeline:
Event Occurs → 0-24 hours → Initial Assertion
Assertion → 2 hours → Challenge Window
No Challenge → Immediate → Resolution Confirmed
With Challenge → Days-Weeks → UMA DVM Vote
```

---

## Fee Structure

### Current Fees (2024)
```
Trading Fees:
- Maker Fee: 0% (promotional)
- Taker Fee: 0% (promotional)

Resolution Fee:
- 2% on net profits at resolution
- Only charged on winning positions
- Calculated as: (winnings - cost basis) × 2%

No Fees For:
- Order cancellation
- Order amendment
- Deposits/withdrawals (only network gas)
```

### Fee Calculation Example
```
Scenario:
- Buy 100 YES tokens at $0.60
- Cost: $60
- YES wins, receive $100

Resolution Fee:
- Profit: $100 - $60 = $40
- Fee: $40 × 2% = $0.80
- Net Payout: $100 - $0.80 = $99.20
```

### Historical Fee Changes
```
2020-2021: Various fee structures tested
2022: Competitive fee reduction
2023: 0% trading fees introduced
2024: 2% resolution fee on profits
```

---

## Smart Contracts

### Core Contracts (Polygon)

#### CTF Exchange
```
Purpose: Handles trading and settlement
Functions:
- matchOrders(): Matches buy/sell orders
- cancelOrder(): Cancels open orders
- cancelOrders(): Batch cancellation
- safeTransferFrom(): Token transfers
```

#### Conditional Tokens Framework
```
Standard: ERC-1155
Purpose: Outcome tokens
Functions:
- splitPosition(): Mint outcome tokens
- mergePosition(): Burn tokens for collateral
- redeemPositions(): Claim winnings after resolution
```

#### Neg Risk CTF Exchange
```
Purpose: Alternative exchange for binary markets
Feature: Allows negative risk positions
Used for: Specific market types
```

### Token Mechanics
```
Minting (Split):
$1 USDC → 1 YES token + 1 NO token

Merging:
1 YES token + 1 NO token → $1 USDC

Redemption (after resolution):
1 Winning token → $1 USDC
1 Losing token → $0 USDC
```

### Contract Addresses (Polygon Mainnet)
```
USDC: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
CTF Exchange: 0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E
Neg Risk CTF: 0xC5d563A36AE78145C45a50134d48A1215220f80a
Conditional Tokens: 0x4D97DCd97eC945f40cF65F87097ACe5EA0476045
```

---

## API Reference

### Endpoints

#### CLOB API
```
Base URL: https://clob.polymarket.com

Public Endpoints:
GET /markets                    List all markets
GET /markets/{condition_id}     Get market details
GET /book                       Get order book
GET /price                      Get current prices
GET /spread                     Get bid-ask spread
GET /midpoint                   Get mid price
GET /trades                     Recent trades
GET /last-trade-price           Last trade price

Authenticated Endpoints:
GET /orders                     Your open orders
POST /order                     Place order
DELETE /order/{id}              Cancel order
DELETE /cancel-all              Cancel all orders
GET /positions                  Your positions
GET /balances                   Your balances
GET /trade-history              Your trades
```

#### Gamma API
```
Base URL: https://gamma-api.polymarket.com

GET /markets                    Market metadata
GET /events                     Event information
GET /markets/{slug}             Market by slug
```

### Authentication
```
Headers Required:
POLY-ADDRESS: Your wallet address
POLY-SIGNATURE: HMAC signature
POLY-TIMESTAMP: Unix timestamp
POLY-API-KEY: API key
POLY-PASSPHRASE: API passphrase

API Key Derivation:
1. Sign typed data with wallet
2. Derive API credentials from signature
3. Use credentials for subsequent requests
```

### WebSocket
```
URL: wss://ws-subscriptions-clob.polymarket.com/ws/

Channels:
- market:{token_id}     Order book updates
- user:{address}        User's orders/fills

Message Types:
- book_snapshot         Full order book
- book_update           Incremental update
- trade                 New trade
- order_update          Order status change
```

### Rate Limits
```
REST API: 100 requests / 10 seconds / IP
WebSocket: 1 connection / API key
Orders: 10 / second / address
```

---

## Wallet & Signatures

### Supported Wallets
```
- MetaMask
- WalletConnect
- Coinbase Wallet
- Rainbow
- Any EVM-compatible wallet
```

### Signature Types
```
Type 0: EOA (Externally Owned Account)
- Standard Ethereum signature
- Most common for regular users

Type 1: Poly Proxy
- Smart contract wallet
- Enables gasless transactions
- Proxy signs on behalf of user

Type 2: Poly Gnosis Safe
- Multi-sig wallet support
- For institutional/team accounts
```

### EIP-712 Order Signing
```
Domain:
{
  name: "Polymarket CTF Exchange",
  version: "1",
  chainId: 137
}

Order Types:
{
  Order: [
    { name: "salt", type: "uint256" },
    { name: "maker", type: "address" },
    { name: "signer", type: "address" },
    { name: "taker", type: "address" },
    { name: "tokenId", type: "uint256" },
    { name: "makerAmount", type: "uint256" },
    { name: "takerAmount", type: "uint256" },
    { name: "expiration", type: "uint256" },
    { name: "nonce", type: "uint256" },
    { name: "feeRateBps", type: "uint256" },
    { name: "side", type: "uint8" },
    { name: "signatureType", type: "uint8" }
  ]
}
```

### Gasless Trading
```
How It Works:
1. User signs order off-chain
2. Polymarket relays to blockchain
3. User pays no gas (Polymarket subsidizes)

Requirements:
- Valid API credentials
- Approved USDC allowance
- Sufficient USDC balance
```

### Approvals Required
```
For Trading:
- USDC approval to CTF Exchange
- Conditional Token approval (for selling)

One-Time Setup:
1. Approve USDC spending
2. Set up API credentials
3. Enable gasless trading (optional)
```

---

## Market Categories

### Politics
```
Types:
- Elections (Presidential, Congressional, International)
- Legislation (Bills, Votes)
- Appointments (Cabinet, Judges)
- Policy decisions

Resolution:
- Official election results
- Congressional records
- Official announcements

Characteristics:
- High liquidity around major events
- Long-duration markets (months)
- High information sensitivity
- Significant volume spikes near resolution
```

### Sports
```
Types:
- Game outcomes
- Championships
- Player statistics
- Awards

Resolution:
- Official league results
- Sports data providers

Characteristics:
- Short duration (hours to weeks)
- High volume during events
- Clear resolution criteria
- Seasonal patterns
```

### Crypto
```
Types:
- Price targets ($BTC to $100k)
- Protocol events (ETF approvals)
- Technical milestones

Resolution:
- Price feeds (Chainlink, CoinGecko)
- Official announcements
- On-chain data

Characteristics:
- 24/7 relevance
- High volatility
- Correlated with crypto markets
```

### Finance/Economics
```
Types:
- Fed decisions (rate cuts/hikes)
- Economic indicators
- Market milestones

Resolution:
- Federal Reserve announcements
- Government data releases

Characteristics:
- Scheduled resolution dates
- Institutional interest
- Low retail participation
```

### Entertainment
```
Types:
- Awards (Oscars, Emmys)
- Box office
- TV ratings
- Celebrity events

Resolution:
- Official awards announcements
- Box office reports

Characteristics:
- Event-driven spikes
- Moderate liquidity
- Cultural relevance
```

### Science/Tech
```
Types:
- Space launches
- Scientific discoveries
- Tech releases

Resolution:
- NASA/official agencies
- Peer-reviewed publications
- Company announcements

Characteristics:
- Long timelines
- Lower liquidity
- Niche audiences
```

---

## Liquidity Dynamics

### Spread Behavior
```
Tight Spreads (<1%):
- High-profile markets
- Near resolution
- Active market makers
- High volume

Wide Spreads (>5%):
- Low interest markets
- Far from resolution
- No market makers
- Low volume
```

### Liquidity Patterns
```
Volume Spikes:
- Breaking news
- Near resolution
- Major events
- Celebrity involvement

Low Activity:
- Overnight (US time)
- Weekends
- Between news cycles
- Long-dated markets
```

### Market Makers
```
Role:
- Provide continuous liquidity
- Earn spread
- Reduce volatility
- Improve price discovery

Strategies:
- Two-sided quotes
- Inventory management
- Dynamic spread adjustment
- Cross-market hedging
```

### Depth Typical Ranges
```
High Liquidity Markets:
- $50k-$500k+ at best levels
- 10+ price levels
- Sub-1% spreads

Medium Liquidity:
- $5k-$50k at best levels
- 5-10 price levels
- 1-3% spreads

Low Liquidity:
- <$5k at best levels
- Few price levels
- >5% spreads
```

---

## Risk Factors

### Market Risks
```
1. RESOLUTION RISK
   - Ambiguous outcomes
   - Disputed resolutions
   - Delayed resolution
   - Market voiding

2. LIQUIDITY RISK
   - Wide spreads
   - Insufficient depth
   - Slippage on large orders
   - Inability to exit

3. VOLATILITY RISK
   - Rapid price movements
   - Gap risk on news
   - Limit order execution

4. CORRELATION RISK
   - Related markets move together
   - Diversification limitations
   - Cascading losses
```

### Technical Risks
```
1. SMART CONTRACT RISK
   - Bugs or vulnerabilities
   - Oracle failures
   - Network congestion

2. API RISK
   - Downtime
   - Rate limiting
   - Connection failures

3. WALLET RISK
   - Private key compromise
   - Approval exploits
   - Phishing attacks
```

### Operational Risks
```
1. REGULATORY RISK
   - Jurisdiction restrictions
   - Platform shutdown
   - Asset freezing

2. COUNTERPARTY RISK
   - Platform insolvency
   - Delayed payouts

3. INFORMATION RISK
   - Insider trading
   - Information asymmetry
   - Fake news manipulation
```

---

## Regulatory Context

### US Regulatory History
```
2022: CFTC Settlement
- $1.4 million fine
- Required to wind down US operations
- Agreed to block US users

Current Status:
- US users technically blocked
- VPN usage common but risky
- No US-compliant operations
```

### Global Status
```
Permitted (generally):
- Most of Europe
- Asia (varies by country)
- South America
- Australia

Restricted:
- United States
- Some EU countries
- Certain Asian jurisdictions

Requirements:
- Age verification (18+)
- AML/KYC (for large volumes)
- Tax reporting (user responsibility)
```

### Legal Classification
```
Varies by Jurisdiction:
- Gambling (some regions)
- Securities (some regions)
- Derivatives (CFTC view)
- Information markets (academic view)
```

---

## Historical Evolution

### Timeline
```
2020:
- Platform launch
- Focus on US election
- Initial market mechanics

2021:
- Polygon migration
- CLOB introduction
- Volume growth

2022:
- CFTC settlement
- US user restrictions
- Continued growth outside US

2023:
- Fee structure changes
- UI improvements
- Market variety expansion

2024:
- Massive election volume
- $1B+ monthly volume
- Mainstream attention
- Celebrity markets
```

### Technical Evolution
```
Early Days:
- AMM-based (like Uniswap)
- Higher fees
- Less efficient pricing

Current:
- CLOB-based
- Zero trading fees
- Professional-grade execution
- API access
```

### Market Evolution
```
Early:
- Primarily US politics
- Simple binary markets
- Limited categories

Current:
- Global events
- Multi-outcome markets
- Sports, crypto, entertainment
- Real-time resolution
```

---

## Trading Patterns

### Common Strategies

#### Arbitrage
```
Binary Arbitrage:
- When YES + NO ≠ $1.00
- Buy both sides for guaranteed profit
- Rare but profitable when found

Cross-Market Arbitrage:
- Same event on different platforms
- Price discrepancies between markets

Resolution Arbitrage:
- Trade on known outcome before resolution
- Requires speed and information
```

#### Market Making
```
Strategy:
- Quote both sides
- Earn spread
- Manage inventory

Key Factors:
- Spread width
- Position limits
- Inventory skew
- Competition
```

#### Directional Trading
```
Information Edge:
- Superior analysis
- Faster information
- Domain expertise

Momentum:
- Follow price trends
- News-based trading

Mean Reversion:
- Trade against extreme moves
- Fade overreactions
```

#### Event-Driven
```
Catalysts:
- Scheduled announcements
- Debates/speeches
- Economic releases
- Sports events

Strategy:
- Position before catalyst
- Trade the reaction
- Fade or follow momentum
```

### Behavioral Patterns
```
Favorite-Longshot Bias:
- Favorites often overpriced
- Longshots underpriced
- Psychological tendency

Recency Bias:
- Overweight recent news
- Underweight base rates

Overconfidence:
- Traders overestimate edge
- Position sizing too aggressive
```

---

## Best Practices

### Risk Management
```
1. Position Sizing
   - Never risk >5% on single market
   - Use Kelly criterion (half-Kelly safer)
   - Account for correlation

2. Diversification
   - Spread across categories
   - Avoid concentrated exposure
   - Balance time horizons

3. Stop Losses
   - Mental stops at minimum
   - Consider automated exits
   - Accept losses early
```

### Execution
```
1. Order Placement
   - Use limit orders
   - Avoid market orders in thin markets
   - Scale into positions

2. Timing
   - Avoid trading on breaking news
   - Wait for spread stabilization
   - Patient execution reduces impact

3. Size Management
   - Check depth before ordering
   - Use iceberg for large orders
   - Split across time
```

### Research
```
1. Resolution Criteria
   - Read market rules carefully
   - Understand edge cases
   - Check resolution source

2. Probability Assessment
   - Use base rates
   - Consider multiple scenarios
   - Update on new information

3. Market Dynamics
   - Watch volume patterns
   - Monitor spread changes
   - Track large traders
```

### Operational
```
1. Security
   - Hardware wallet recommended
   - Unique strong passwords
   - Enable all security features

2. Record Keeping
   - Track all trades
   - Calculate true P&L
   - Document for taxes

3. Monitoring
   - Set price alerts
   - Monitor positions regularly
   - Have exit plans ready
```

---

## Quick Reference

### Key Numbers
```
Chain ID: 137 (Polygon)
USDC Decimals: 6
Min Tick: $0.001
Min Order: $0.01
Max Order: $100,000
Resolution Fee: 2% on profits
Challenge Window: 2 hours
API Rate Limit: 100/10s
```

### Key URLs
```
CLOB API: https://clob.polymarket.com
Gamma API: https://gamma-api.polymarket.com
WebSocket: wss://ws-subscriptions-clob.polymarket.com/ws/
Website: https://polymarket.com
Docs: https://docs.polymarket.com
```

### Key Formulas
```
Implied Probability = Price
Decimal Odds = 1 / Price
Expected Value = (Prob × Payout) - Cost
Kelly Fraction = (bp - q) / b
  where b = odds-1, p = win prob, q = 1-p
Binary Constraint = YES + NO = 1
```

---

*Last Updated: December 2024*
*This document represents accumulated knowledge about Polymarket and may not reflect the most current state of the platform.*
