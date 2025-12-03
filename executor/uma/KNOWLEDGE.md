# UMA Protocol - Complete Knowledge Base
## Universal Market Access - Optimistic Oracle & Dispute Resolution

---

# TABLE OF CONTENTS

1. [Protocol Overview](#1-protocol-overview)
2. [Core Architecture](#2-core-architecture)
3. [Optimistic Oracle (OO)](#3-optimistic-oracle-oo)
4. [Data Verification Mechanism (DVM)](#4-data-verification-mechanism-dvm)
5. [Price Identifiers & UMIP Process](#5-price-identifiers--umip-process)
6. [Economic Security Model](#6-economic-security-model)
7. [UMA Token Economics](#7-uma-token-economics)
8. [Smart Contract Architecture](#8-smart-contract-architecture)
9. [Dispute Resolution Deep Dive](#9-dispute-resolution-deep-dive)
10. [Financial Products](#10-financial-products)
11. [oSnap: Optimistic Governance](#11-osnap-optimistic-governance)
12. [Oval: MEV Protection](#12-oval-mev-protection)
13. [Integration Patterns](#13-integration-patterns)
14. [Security Model](#14-security-model)
15. [Governance](#15-governance)
16. [Historical Evolution](#16-historical-evolution)
17. [Ecosystem & Use Cases](#17-ecosystem--use-cases)
18. [Comparison with Other Oracles](#18-comparison-with-other-oracles)
19. [Risk Factors](#19-risk-factors)
20. [Best Practices](#20-best-practices)

---

# 1. PROTOCOL OVERVIEW

## What is UMA?

UMA (Universal Market Access) is a decentralized protocol that enables:
1. **Optimistic Oracle** - Data verification with economic guarantees
2. **Dispute Resolution** - Decentralized arbitration via token holder voting
3. **Financial Contracts** - Synthetic assets, prediction markets, insurance

## Core Philosophy

**"Optimistic" Design Pattern:**
- Assume assertions are truthful by default
- Only verify when economically challenged
- Disputes are expensive, making lying unprofitable
- Truth emerges through game-theoretic incentives

## Key Innovation

Traditional oracles: Push data on-chain constantly (expensive, attack surface)
UMA's approach: Assert data, challenge if wrong (efficient, economically secure)

```
Traditional Oracle:         UMA Optimistic Oracle:

Price Feed → On-chain      Assertion → Challenge Window → Resolution
(constant updates)         (only disputed if wrong)

Cost: High                 Cost: Low (disputes rare)
Security: Technical        Security: Economic
```

## Protocol Statistics (Reference)

- Launched: December 2020 (mainnet)
- Total Value Secured: Billions USD historically
- Disputes: <1% of assertions disputed
- Dispute Resolution: ~48 hours typical
- Chains: Ethereum, Polygon, Arbitrum, Optimism, Boba, others

---

# 2. CORE ARCHITECTURE

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    UMA PROTOCOL STACK                        │
├─────────────────────────────────────────────────────────────┤
│  APPLICATIONS                                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Polymarket│ │ Sherlock│ │  Across │ │  oSnap  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
├───────┴──────────┴──────────┴──────────┴────────────────────┤
│  OPTIMISTIC ORACLE V3                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Assert → Challenge Window → Settlement/Dispute       │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  DATA VERIFICATION MECHANISM (DVM)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  UMA Token Holder Voting (Schelling Point)            │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ECONOMIC SECURITY                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Bonds + Fees + Slashing = Cost of Corruption > Profit│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Two-Layer Oracle System

### Layer 1: Optimistic Oracle (Fast Path)
- Handles 99%+ of price requests
- 2-hour default challenge window
- No voting required if undisputed
- Proposer posts bond, gets it back if correct

### Layer 2: DVM (Dispute Path)
- Activated only when disputes occur
- 48-96 hour voting period
- All UMA token holders can vote
- Schelling point mechanism

## Data Flow

```
1. Request: Protocol needs data (e.g., "Did X happen?")
       ↓
2. Assertion: Proposer asserts answer + posts bond
       ↓
3. Challenge Window: Anyone can dispute (2 hours default)
       ↓
   ┌─────────────────┬─────────────────┐
   │ No Dispute      │ Dispute Filed   │
   │                 │                 │
   ↓                 ↓                 │
4a. Settlement     4b. DVM Vote       │
   (proposer wins)     (48-96 hrs)    │
                       ↓              │
                   5. Resolution      │
                   (winner gets bonds)│
   └─────────────────┴─────────────────┘
```

---

# 3. OPTIMISTIC ORACLE (OO)

## Overview

The Optimistic Oracle is UMA's primary interface for data requests. It operates on the principle that most assertions are truthful, so verifying every data point is wasteful.

## Versions

### OO v1 (Legacy)
- Original implementation
- Price request model
- Used by Polymarket initially

### OO v2
- Improved gas efficiency
- Better callback patterns
- Enhanced dispute handling

### OO v3 (Current)
- Assertion-based model
- Flexible claim types
- Native escalation manager support
- Used by modern integrations

## Key Concepts

### Assertions
An assertion is a claim about reality:
- "ETH price was $2000 on Jan 1, 2024"
- "Team A won the game"
- "Insurance claim is valid"
- "Governance proposal passed"

### Assertion Lifecycle

```
State: ASSERTED
  ↓ (challenge window)
State: DISPUTED (if challenged)
  ↓ (DVM voting)
State: RESOLVED
  ↓
State: SETTLED (bonds distributed)
```

### Bonds

**Proposer Bond:**
- Posted when making assertion
- Returned if assertion is truthful
- Forfeited if assertion is false
- Minimum bond set by protocol

**Disputer Bond:**
- Posted when challenging assertion
- Returned if dispute is successful
- Forfeited if dispute fails
- Usually equals proposer bond

### Challenge Window

Default: 2 hours (7200 seconds)
Configurable per integration
Purpose: Allow time for disputes

```
|-------- Challenge Window --------|
|                                  |
Assert                          Settle
Time                             Time

If disputed during window → DVM
If undisputed → Auto-settle
```

## OO v3 Interface

### Core Functions

```solidity
// Make an assertion
function assertTruth(
    bytes memory claim,           // What you're asserting
    address asserter,             // Who made it
    address callbackRecipient,    // Who to notify
    address escalationManager,    // Custom dispute handling
    uint64 liveness,              // Challenge window (seconds)
    IERC20 currency,              // Bond currency
    uint256 bond,                 // Bond amount
    bytes32 identifier,           // Price identifier
    bytes32 domainId              // Application domain
) external returns (bytes32 assertionId);

// Dispute an assertion
function disputeAssertion(
    bytes32 assertionId,
    address disputer
) external;

// Settle after liveness
function settleAssertion(
    bytes32 assertionId
) external;

// Get assertion result
function getAssertionResult(
    bytes32 assertionId
) external view returns (bool);
```

### Callbacks

```solidity
interface OptimisticOracleV3CallbackRecipient {
    // Called when assertion is resolved
    function assertionResolvedCallback(
        bytes32 assertionId,
        bool assertedTruthfully
    ) external;

    // Called when assertion is disputed
    function assertionDisputedCallback(
        bytes32 assertionId
    ) external;
}
```

## Liveness (Challenge Window) Considerations

| Use Case | Recommended Liveness | Rationale |
|----------|---------------------|-----------|
| Prediction markets | 2 hours | Quick settlement, active monitoring |
| Insurance claims | 24-72 hours | Complex verification needed |
| Governance | 24-48 hours | Allow community review |
| Cross-chain bridges | 20-60 minutes | Speed critical, high monitoring |
| KPI options | 2-4 hours | Standard verification |

---

# 4. DATA VERIFICATION MECHANISM (DVM)

## Overview

The DVM is UMA's final arbitration layer - a decentralized court where UMA token holders vote on disputed questions.

## How It Works

### Schelling Point Mechanism

Voters independently select what they believe is the "obvious" correct answer. Those who vote with the majority are rewarded; those who don't are penalized.

```
Question: "Was ETH price above $2000 on date X?"

Voter A thinks: "I'll vote YES because it's true"
Voter B thinks: "I'll vote YES because others will vote YES"
Voter C thinks: "I'll vote YES because it's verifiable"

Result: Majority votes YES (Schelling point)
```

### Voting Process

```
Day 0: Dispute filed
       ↓
Day 0-2: Commit Phase
         - Voters submit encrypted votes
         - Hash of (vote + salt)
         ↓
Day 2-4: Reveal Phase
         - Voters reveal votes
         - Must match committed hash
         ↓
Day 4+: Resolution
        - Majority answer wins
        - Rewards distributed
```

### Vote Encryption

```
Commit: keccak256(vote, price, salt)
Reveal: (vote, price, salt)

Why encrypt?
- Prevents vote copying
- Ensures independent judgment
- Maintains Schelling point integrity
```

## Voting Mechanics

### Who Can Vote?
- Any UMA token holder
- Tokens must be staked/delegated
- Voting power = token balance at snapshot

### Voting Rewards

**Correct Voters:**
- Receive pro-rata share of:
  - Loser's slashed stake
  - Protocol fees
  - Inflation rewards

**Incorrect Voters:**
- Lose portion of staked tokens
- Miss out on rewards

### Reward Calculation

```
Your Reward = (Your Correct Votes / Total Correct Votes) × Reward Pool

Reward Pool = Slashed Stakes + Fees + Emissions
```

## DVM Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Commit Period | 24 hours | Time to submit votes |
| Reveal Period | 24 hours | Time to reveal votes |
| GAT (Governance Attention Threshold) | 5% | Minimum participation |
| Slash Amount | Variable | Penalty for wrong votes |
| Minimum Bond | ~$1500 USDC equiv | Prevent spam disputes |

## Price Identifiers

The DVM can resolve various question types:

### Numerical Prices
- `ETH/USD` - Ethereum price
- `BTC/USD` - Bitcoin price
- Custom price feeds

### Binary Outcomes
- `YES_OR_NO_QUERY` - True/false questions
- Used by prediction markets

### Custom Identifiers
- Defined via UMIP process
- Application-specific logic

---

# 5. PRICE IDENTIFIERS & UMIP PROCESS

## Price Identifiers

A price identifier defines:
1. What data is being requested
2. How to calculate/verify it
3. Where to source the data
4. Edge case handling

## Common Identifiers

### YES_OR_NO_QUERY
```
Purpose: Binary outcomes
Returns: 1 (YES), 0 (NO), or 0.5 (UNKNOWN/EARLY)
Used by: Prediction markets, insurance

Rules:
- Question must be unambiguous
- Must be verifiable by voters
- Return 0.5 if genuinely unknowable
```

### ASSERT_TRUTH
```
Purpose: General assertions
Returns: true or false
Used by: OO v3, general oracle queries

Rules:
- Assertion must be clear English
- Verifiable with public information
- Binary resolution
```

### Numerical Identifiers
```
ETH/USD:
- Source: Major exchanges (Coinbase, Binance, etc.)
- Calculation: Median of sources
- Precision: 18 decimals

GASETH-TWAP-1Mx1M:
- Gas price in ETH
- Time-weighted average
```

## UMIP Process

**UMIP = UMA Improvement Proposal**

### Purpose
- Add new price identifiers
- Modify protocol parameters
- Upgrade contracts
- Governance changes

### UMIP Structure

```markdown
# UMIP-XXX: [Title]

## Summary
Brief description

## Motivation
Why this is needed

## Technical Specification
- Price identifier name
- Markets/pairs covered
- Data sources (priority order)
- Price calculation methodology
- Edge cases and handling

## Rationale
Why this approach

## Implementation
Contract changes needed

## Security Considerations
Risk analysis
```

### UMIP Lifecycle

```
1. Draft → Discourse discussion
2. Review → Community feedback
3. Snapshot → Off-chain vote
4. Implementation → Technical work
5. Deployment → On-chain execution
```

## Registered Identifiers (Partial List)

| Identifier | Type | Use Case |
|------------|------|----------|
| YES_OR_NO_QUERY | Binary | Prediction markets |
| ASSERT_TRUTH | Binary | General assertions |
| SHERLOCK_CLAIM | Binary | Audit claims |
| ETH/USD | Price | DeFi protocols |
| ACROSS-V2 | Custom | Bridge verification |
| ZODIAC | Custom | Governance |

---

# 6. ECONOMIC SECURITY MODEL

## Core Principle

**Cost of Corruption > Profit from Corruption**

UMA's security doesn't rely on honest participants - it relies on making dishonesty unprofitable.

## Security Budget

```
Security Budget = Value that can be safely secured

For UMA:
Security Budget ≈ 0.5 × (UMA Market Cap) × (Participation Rate)

Why 0.5x?
- Cost to bribe 51% of voters
- Conservative estimate
```

## Attack Cost Analysis

### Attacking the Optimistic Oracle

**Scenario:** Bad actor wants to settle false assertion

Cost to Attack:
```
1. Proposer Bond: $X (lost when disputed)
2. Must bribe DVM voters:
   Bribe Cost = 51% × Voting Stake × Expected Return
3. Risk of failed bribe (voters defect)
4. Reputation damage

Total Attack Cost >> Potential Profit
```

### Attacking the DVM

**Scenario:** Control majority vote

```
Option A: Acquire 51% UMA
- Cost: ~50% of market cap
- Detection: Price impact, governance visibility
- Outcome: Token value crashes, attack unprofitable

Option B: Bribe voters
- Cost: Must exceed their staking rewards + slashing risk
- Detection: Unusual voting patterns
- Outcome: Protocol can respond, upgrade

Both options: Attack cost exceeds profit for reasonable TVL
```

## Bond Economics

### Minimum Bond Calculation

```
Minimum Bond should satisfy:
Bond > (Expected Profit from False Assertion) / (Probability of Dispute)

If disputes are ~90% likely for false assertions:
Bond > 1.1 × Profit

Plus: DVM fees (~$1500 USDC equivalent)
```

### Bond Sizing by Application

| Application | Typical Bond | Rationale |
|-------------|-------------|-----------|
| Polymarket | $2-5 | High frequency, active monitors |
| Insurance | $500-5000 | High stakes, thorough review |
| Governance | $1000-10000 | Critical decisions |
| Bridges | $5000-50000 | Maximum security needed |

## Incentive Alignment

### Proposers
- Earn: Bond return + potential rewards
- Risk: Bond loss if wrong
- Incentive: Only propose truthful assertions

### Disputers
- Earn: Proposer's bond if dispute succeeds
- Risk: Own bond if dispute fails
- Incentive: Only dispute false assertions

### Voters
- Earn: Rewards for correct votes
- Risk: Slashing for incorrect votes
- Incentive: Vote with majority (truth)

---

# 7. UMA TOKEN ECONOMICS

## Token Overview

| Property | Value |
|----------|-------|
| Name | UMA |
| Type | ERC-20 |
| Total Supply | ~120M (inflationary) |
| Inflation | 0.05% per vote |
| Primary Use | DVM Voting |

## Token Utility

### 1. Voting Power
- Vote on disputed assertions
- Proportional to holdings
- Must stake to participate

### 2. Governance
- Protocol upgrades
- Parameter changes
- UMIP approval

### 3. Economic Security
- Backs oracle security
- Higher market cap = more security

## Staking Mechanism

### How Staking Works

```
1. Stake UMA tokens
2. Receive voting rights
3. Participate in votes
4. Earn rewards for correct votes
5. Risk slashing for wrong votes
```

### Staking Parameters

| Parameter | Value |
|-----------|-------|
| Unstaking Period | 7 days |
| Minimum Stake | None |
| Slashing Rate | Variable per vote |

## Reward Distribution

### Sources of Rewards

1. **Inflation Rewards**
   - 0.05% of supply per resolved vote
   - Distributed to correct voters

2. **Dispute Fees**
   - Fixed fee per dispute
   - Goes to correct voters

3. **Slashed Stakes**
   - From incorrect voters
   - Redistributed to correct voters

### Reward Calculation

```
Your Reward = (Your Stake / Total Correct Stake) × Total Rewards

Where:
Total Rewards = Inflation + Fees + Slashed Stakes
```

## Token Distribution

### Initial Distribution (2020)
- Team/Advisors: ~35%
- Investors: ~15%
- Ecosystem: ~20%
- Risk Labs Foundation: ~30%

### Current Distribution
- More decentralized over time
- Active governance participation
- Wide holder base

---

# 8. SMART CONTRACT ARCHITECTURE

## Core Contracts

### OptimisticOracleV3

**Purpose:** Main oracle interface

**Key State:**
```solidity
struct Assertion {
    EscalationManagerSettings escalationManagerSettings;
    address asserter;
    uint64 assertionTime;
    bool settled;
    IERC20 currency;
    uint64 expirationTime;
    bool settlementResolution;
    bytes32 domainId;
    bytes32 identifier;
    uint256 bond;
    address callbackRecipient;
    address disputer;
}

mapping(bytes32 => Assertion) public assertions;
```

### Voting (DVM)

**Purpose:** Token holder voting

**Key Functions:**
```solidity
function commitVote(
    bytes32 identifier,
    uint256 time,
    bytes32 hash
) external;

function revealVote(
    bytes32 identifier,
    uint256 time,
    int256 price,
    int256 salt
) external;

function retrieveRewards(
    address voterAddress,
    uint256 roundId,
    PendingRequest[] memory toRetrieve
) external returns (FixedPoint.Unsigned memory);
```

### Store

**Purpose:** Fee collection and distribution

**Key Functions:**
```solidity
function payOracleFees() external payable;
function computeFinalFee(address currency) external view returns (FixedPoint.Unsigned memory);
```

### IdentifierWhitelist

**Purpose:** Manage approved price identifiers

**Key Functions:**
```solidity
function addSupportedIdentifier(bytes32 identifier) external;
function isIdentifierSupported(bytes32 identifier) external view returns (bool);
```

### AddressWhitelist

**Purpose:** Manage approved collateral currencies

## Contract Addresses (Ethereum Mainnet)

| Contract | Address |
|----------|---------|
| OptimisticOracleV3 | 0xfb55F43fB9F48F63f9269DB7Dde3BbBe1ebDC0dE |
| Voting (DVM) | 0x004395edb43EFca9885CEdad51EC9fAf93Bd34ac |
| Store | 0x54f44eA3D2e7aA0ac089c4d8F7C93C27844057BF |
| IdentifierWhitelist | 0xcF649d9Da4D1362C4DAEa67573430Bd6f945e570 |
| Finder | 0x40f941E48A552bF496B154Af6bf55725f18D77c3 |

## Multi-Chain Deployments

UMA is deployed on:
- Ethereum Mainnet
- Polygon
- Arbitrum
- Optimism
- Boba Network
- Gnosis Chain
- Avalanche

Each deployment has chain-specific addresses.

---

# 9. DISPUTE RESOLUTION DEEP DIVE

## Dispute Flow

### Step 1: Dispute Filing

```solidity
// Disputer calls
optimisticOracle.disputeAssertion(assertionId, disputerAddress);

// Requires:
// - Assertion exists and not expired
// - Challenge window still open
// - Disputer has bond amount
```

### Step 2: DVM Request

The OO automatically:
1. Forwards question to DVM
2. Transfers both bonds to DVM
3. Pauses assertion settlement

### Step 3: Voting

```
Commit Phase (24h):
- Voters hash their votes
- Submit commitments on-chain
- Cannot see others' votes

Reveal Phase (24h):
- Voters reveal votes with salt
- Must match commitment
- Tallying occurs
```

### Step 4: Resolution

```solidity
// After voting concludes
bool result = dvm.getPrice(identifier, timestamp);

// OO receives result
// Settles assertion accordingly
// Distributes bonds
```

## Dispute Outcomes

### Scenario A: Proposer Was Correct
```
Disputer loses bond → Goes to proposer
Proposer keeps bond → Returns to proposer
Assertion settles as originally proposed
```

### Scenario B: Disputer Was Correct
```
Proposer loses bond → Goes to disputer
Disputer keeps bond → Returns to disputer
Assertion settles as disputed (opposite)
```

## Dispute Economics

### Break-Even Analysis

```
For Disputer:
Expected Value = P(win) × Proposer Bond - P(lose) × Own Bond - Gas Costs

Dispute if:
P(win) > (Own Bond + Gas) / (Proposer Bond + Own Bond)

For typical equal bonds:
P(win) > 50% + (Gas / 2×Bond)
```

### Dispute Costs

| Component | Approximate Cost |
|-----------|-----------------|
| Gas (dispute tx) | $20-100 |
| Bond | Variable (min ~$1500) |
| Time | 48-96 hours |
| Opportunity | Bond locked |

## Edge Cases

### Early Resolution

Some assertions can resolve early if:
- Proposer admits error
- Clear evidence emerges
- Escalation manager intervenes

### Ties

If DVM vote is tied:
- Default to "unknown" resolution
- May use 0.5 for numerical prices
- Application handles accordingly

### No Quorum

If insufficient participation:
- Vote may be extended
- GAT (5%) must be reached
- Protocol has escalation procedures

---

# 10. FINANCIAL PRODUCTS

## Overview

UMA enables various financial products using its oracle infrastructure:

## Long Short Pair (LSP)

### Concept
Two tokens representing opposite sides of an outcome:
- Long Token: Pays if price goes UP
- Short Token: Pays if price goes DOWN

### Mechanics
```
Mint: Deposit $1 → Receive 1 Long + 1 Short
Redeem: Return 1 Long + 1 Short → Get $1 back
Settle: At expiry, Long + Short = $1 based on price
```

### Example
```
Underlying: ETH/USD
Strike: $2000
Expiry: 30 days

If ETH = $2500 at expiry:
- Long token = $1 (won)
- Short token = $0 (lost)

If ETH = $1500 at expiry:
- Long token = $0 (lost)
- Short token = $1 (won)
```

## Range Tokens

### Concept
Tokens that pay based on price being within a range.

### Mechanics
```
Range: $1800 - $2200
If price in range: Token = $1
If price outside: Token = $0
```

### Use Cases
- Yield enhancement
- Covered calls on steroids
- Range-bound market bets

## Success Tokens

### Concept
Tokens that pay based on achievement of a goal.

### Example
```
"Project X reaches 1M users by Dec 31"
If achieved: Token = $1
If not: Token = $0
```

### Use Cases
- Project incentive alignment
- KPI-linked compensation
- Milestone-based funding

## KPI Options

### Concept
Tokens whose payout scales with a KPI metric.

### Mechanics
```
KPI: Total Value Locked (TVL)
Payout Formula: min(TVL / $100M, 1) × $1

If TVL = $50M → Payout = $0.50
If TVL = $100M+ → Payout = $1.00
```

### Use Cases
- Incentivizing protocol growth
- Aligning community with metrics
- Performance-based rewards

## Call/Put Options

### Call Option
```
Right to buy at strike price

If Spot > Strike: Option = Spot - Strike
If Spot ≤ Strike: Option = 0
```

### Put Option
```
Right to sell at strike price

If Spot < Strike: Option = Strike - Spot
If Spot ≥ Strike: Option = 0
```

## Prediction Market Tokens

Used by platforms like Polymarket:

```
Binary Outcome:
- YES token: Pays $1 if event occurs
- NO token: Pays $1 if event doesn't occur

Constraint: YES + NO prices should ≈ $1
```

---

# 11. oSNAP: OPTIMISTIC GOVERNANCE

## Overview

oSnap = Optimistic Snapshot Execution

Allows DAOs to execute on-chain transactions based on off-chain Snapshot votes.

## Problem Solved

Traditional flow:
```
Snapshot Vote → Pass → Manual Multisig Execution → Hope they do it
```

oSnap flow:
```
Snapshot Vote → Pass → Automatic On-chain Execution (via UMA)
```

## How It Works

### Step 1: Proposal
```
DAO creates Snapshot proposal
Includes transactions to execute
Vote occurs off-chain (gasless)
```

### Step 2: Assertion
```
After vote passes:
Anyone can assert "Vote X passed"
Posts bond with UMA OO
```

### Step 3: Challenge Window
```
Default: 24-72 hours
Anyone can dispute if:
- Vote didn't actually pass
- Transactions don't match proposal
- Other issues
```

### Step 4: Execution
```
If undisputed:
- oSnap module executes transactions
- Automatic, trustless, permissionless
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Snapshot   │────▶│   oSnap     │────▶│   Gnosis    │
│   (Vote)    │     │  (Assert)   │     │   Safe      │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                   ┌──────▼──────┐
                   │  UMA OO     │
                   │  (Verify)   │
                   └─────────────┘
```

## Security Model

**Bond:** Proposer stakes funds
**Challenge:** Anyone can dispute
**Verification:** UMA DVM if disputed
**Result:** Trustless governance execution

## Adopters
- Across Protocol
- Sherlock
- Many DAOs via Zodiac

---

# 12. OVAL: MEV PROTECTION

## Overview

Oval = Oracle Value Aggregation Layer

Protects protocols from MEV (Miner/Maximal Extractable Value) attacks on oracle updates.

## Problem Solved

### Traditional Oracle MEV
```
1. Oracle about to update price
2. Searcher sees update in mempool
3. Searcher front-runs, executes trade
4. Oracle updates
5. Searcher profits from price movement
```

### With Oval
```
1. Oracle update goes through Oval
2. Oval auctions the right to backrun
3. Revenue goes to protocol, not searchers
4. Protocol captures own MEV
```

## How It Works

### Price Update Flow
```
Chainlink  ──┐
             │
Pyth    ────▶│  Oval  ──▶  Protocol
             │
Chronicle ──┘
```

### MEV Auction
```
1. Oval holds price update briefly
2. Searchers bid for backrun rights
3. Highest bidder wins
4. Revenue to protocol treasury
```

## Benefits

| Without Oval | With Oval |
|-------------|-----------|
| MEV to searchers | MEV to protocol |
| $0 captured | Up to 90% captured |
| Adversarial | Aligned |

## Technical Details

- Delay: ~12 seconds (configurable)
- Auction: Flashbots MEV-Share
- Integration: Wrap existing oracle

---

# 13. INTEGRATION PATTERNS

## Basic OO Integration

### Requesting Data

```solidity
// 1. Define your assertion
bytes memory claim = abi.encodePacked(
    "The price of ETH was above $2000 on ",
    "January 1, 2024"
);

// 2. Calculate bond
uint256 bond = oo.getMinimumBond(currency);

// 3. Assert truth
bytes32 assertionId = oo.assertTruth(
    claim,
    msg.sender,      // asserter
    address(this),   // callback recipient
    address(0),      // escalation manager (none)
    7200,            // 2 hour liveness
    currency,
    bond,
    "ASSERT_TRUTH",
    bytes32(0)       // domain
);
```

### Handling Callbacks

```solidity
contract MyProtocol is OptimisticOracleV3CallbackRecipient {

    function assertionResolvedCallback(
        bytes32 assertionId,
        bool assertedTruthfully
    ) external override {
        require(msg.sender == address(oo), "Only OO");

        if (assertedTruthfully) {
            // Assertion was correct
            executePositiveOutcome(assertionId);
        } else {
            // Assertion was disputed and rejected
            executeNegativeOutcome(assertionId);
        }
    }

    function assertionDisputedCallback(
        bytes32 assertionId
    ) external override {
        require(msg.sender == address(oo), "Only OO");
        // Handle dispute (optional)
        emit AssertionDisputed(assertionId);
    }
}
```

## Escalation Manager Pattern

Custom dispute handling logic:

```solidity
interface EscalationManagerInterface {
    function getAssertionPolicy(
        bytes32 assertionId
    ) external view returns (AssertionPolicy memory);

    function assertionResolvedCallback(
        bytes32 assertionId,
        bool assertedTruthfully
    ) external;

    function assertionDisputedCallback(
        bytes32 assertionId
    ) external;
}
```

## Polymarket Integration Pattern

```
1. Market Created
   - Define question
   - Set resolution criteria

2. Trading Phase
   - Users buy YES/NO tokens
   - CLOB matches orders

3. Resolution Request
   - Question deadline reached
   - Request sent to UMA OO

4. Assertion
   - Proposer asserts outcome
   - Posts bond

5. Challenge Window
   - 2 hours for disputes

6. Settlement
   - If no dispute: Settle
   - If disputed: DVM votes

7. Token Redemption
   - Winners redeem tokens
   - $1 per winning token
```

## Insurance Integration Pattern

```solidity
contract InsuranceProtocol {
    function fileClaim(bytes memory claimData) external {
        // User files insurance claim
        bytes memory claim = abi.encodePacked(
            "Insurance claim is valid: ",
            claimData
        );

        // Higher bond for insurance (more at stake)
        uint256 bond = 5000e6; // $5000 USDC

        oo.assertTruth(
            claim,
            msg.sender,
            address(this),
            insuranceEscalationManager,
            86400, // 24 hour liveness
            usdc,
            bond,
            "SHERLOCK_CLAIM",
            bytes32(0)
        );
    }
}
```

---

# 14. SECURITY MODEL

## Trust Assumptions

### What UMA Assumes
1. Majority of UMA token holders are rational
2. Economic incentives align with truth
3. Information is publicly available
4. Disputes will be filed for false assertions

### What UMA Does NOT Assume
1. All participants are honest
2. No collusion exists
3. Oracles are always correct initially

## Attack Vectors & Mitigations

### 1. False Assertion Attack

**Attack:** Propose false data, hope no one disputes

**Mitigation:**
- Bond loss (100% of bond)
- Active disputer community
- Monitoring bots
- Financial incentive to dispute

### 2. 51% Token Attack

**Attack:** Acquire majority UMA, control votes

**Mitigation:**
- Massive capital requirement
- Price impact would exceed profit
- Token devaluation post-attack
- Community can fork

### 3. Bribery Attack

**Attack:** Pay voters to vote incorrectly

**Mitigation:**
- Must bribe 51% of participants
- Slashing risk for voters
- Reputation damage
- Commit-reveal prevents coordination

### 4. Griefing Attack

**Attack:** Dispute valid assertions to waste time/money

**Mitigation:**
- Disputer bond lost on failed dispute
- DVM fees paid by loser
- Economic disincentive

### 5. Front-Running

**Attack:** See pending assertion, act on information

**Mitigation:**
- Challenge window allows correction
- Multi-block finality
- Application-level protection

## Security Properties

| Property | Mechanism |
|----------|-----------|
| Liveness | Economic incentive to propose |
| Correctness | Dispute mechanism |
| Finality | DVM resolution is final |
| Censorship Resistance | Permissionless assertion |

## Audit History

UMA contracts have been audited by:
- OpenZeppelin
- Trail of Bits
- Others

Ongoing bug bounty program via Immunefi.

---

# 15. GOVERNANCE

## Governance Structure

### Risk Labs Foundation
- Non-profit entity
- Core development
- Protocol stewardship
- No direct governance power

### UMA Token Holders
- Full governance rights
- Vote on UMIPs
- Vote in DVM
- Control protocol parameters

## Governance Process

### UMIP Lifecycle

```
1. Idea
   ↓ (Discussion on Discourse)
2. Draft UMIP
   ↓ (Community feedback)
3. Final UMIP
   ↓ (Snapshot vote)
4. Approved
   ↓ (Implementation)
5. Deployed
```

### Voting Mechanisms

**Snapshot (Off-chain):**
- Used for governance proposals
- Gasless voting
- Signal + binding with oSnap

**DVM (On-chain):**
- Used for dispute resolution
- Requires staking
- Direct economic incentives

## Key Parameters

| Parameter | Current Value | Governance |
|-----------|---------------|------------|
| Final Fee | ~$1500 equiv | UMIP |
| GAT | 5% | UMIP |
| Inflation Rate | 0.05% | UMIP |
| Liveness (default) | 2 hours | Per-integration |

## Historical Governance Decisions

- Migration to OO v3
- Multi-chain deployments
- New price identifier additions
- Fee adjustments
- Contract upgrades

---

# 16. HISTORICAL EVOLUTION

## Timeline

### 2018
- Concept development
- Risk Labs founded

### 2019
- Whitepaper published
- Initial design of DVM

### 2020
- Mainnet launch (Q4)
- First synthetic tokens
- $UMA token launch

### 2021
- LSP (Long Short Pair) launch
- KPI Options introduction
- Multi-chain expansion begins
- Polymarket integration

### 2022
- OO v2 launch
- oSnap introduction
- Continued expansion

### 2023
- OO v3 launch
- Oval MEV protection
- Across Protocol growth
- Enhanced efficiency

### 2024
- Continued adoption
- Cross-chain optimistic oracle
- New product integrations

## Major Milestones

| Date | Event | Significance |
|------|-------|--------------|
| Dec 2020 | Mainnet Launch | Protocol goes live |
| Jan 2021 | Polymarket Integration | Major use case validation |
| Jul 2021 | KPI Options | Novel DeFi primitive |
| Dec 2021 | oSnap Launch | Trustless governance |
| 2022 | OO v2 | Improved efficiency |
| 2023 | OO v3 | Current version |
| 2023 | Oval | MEV protection |

---

# 17. ECOSYSTEM & USE CASES

## Major Integrations

### Polymarket
```
Use: Prediction market resolution
Volume: Billions in markets
Integration: OO for binary outcomes
```

### Across Protocol
```
Use: Cross-chain bridge verification
Role: Verify bridge intents
Integration: OO v3 with custom escalation
```

### Sherlock
```
Use: Audit competition resolution
Role: Verify bug validity
Integration: OO for claims verification
```

### Cozy Finance
```
Use: Insurance claims
Role: Verify insurance conditions
Integration: OO for claim settlement
```

### DAOs (via oSnap)
```
Use: Trustless governance execution
Role: Execute Snapshot votes on-chain
Integration: oSnap module
```

## Use Case Categories

### 1. Prediction Markets
- Binary outcomes
- Multi-outcome markets
- Long-tail events
- Political, sports, crypto

### 2. Insurance/Protection
- Smart contract coverage
- Audit claim verification
- Parametric insurance

### 3. Cross-Chain
- Bridge verification
- Intent fulfillment
- Message passing

### 4. Governance
- Vote execution
- Proposal verification
- Emergency actions

### 5. Synthetic Assets
- Price-tracking tokens
- Options and futures
- Custom derivatives

### 6. Data Verification
- Off-chain data on-chain
- Real-world events
- Custom oracle needs

---

# 18. COMPARISON WITH OTHER ORACLES

## Oracle Landscape

| Oracle | Model | Security | Speed |
|--------|-------|----------|-------|
| UMA | Optimistic | Economic | 2hr+ |
| Chainlink | Push/Pull | DON consensus | Seconds |
| Pyth | Push | Validator consensus | Sub-second |
| API3 | First-party | Provider reputation | Seconds |
| Band | IBC-based | Validator consensus | Seconds |

## UMA vs Chainlink

| Aspect | UMA | Chainlink |
|--------|-----|-----------|
| Model | Optimistic | Real-time feeds |
| Data Types | Arbitrary | Predefined |
| Cost | Low (disputes rare) | Ongoing feed costs |
| Speed | Hours (liveness) | Seconds |
| Customization | High | Limited |
| Best For | Events, outcomes | Prices, constant data |

## When to Use UMA

**Good fit:**
- Binary outcomes (yes/no questions)
- Infrequent data needs
- Custom/novel data types
- Human-interpretable questions
- Where challenge window is acceptable

**Less ideal:**
- Real-time price feeds
- High-frequency updates
- Sub-second requirements
- Already supported by push oracles

## Complementary Usage

Many protocols use multiple oracles:
- Chainlink for live prices
- UMA for event resolution
- Pyth for DeFi
- UMA for governance

---

# 19. RISK FACTORS

## Protocol Risks

### 1. Smart Contract Risk
- Bugs in OO or DVM
- Upgrade vulnerabilities
- Integration mistakes

**Mitigation:** Audits, bug bounties, formal verification

### 2. Economic Attack Risk
- Insufficient bond sizes
- Token concentration
- Voter apathy

**Mitigation:** Dynamic bonds, participation incentives

### 3. Oracle Manipulation
- Coordinated false assertions
- Timing attacks
- Information asymmetry

**Mitigation:** Challenge mechanism, monitoring

## Market Risks

### 1. UMA Token Price
- Security scales with market cap
- Price crash = reduced security
- Circular dependency

### 2. Gas Prices
- High gas = expensive disputes
- May discourage legitimate disputes
- Multi-chain helps

### 3. Liquidity
- Bond currency availability
- UMA trading liquidity
- DeFi composability

## Operational Risks

### 1. Key Management
- Proposer key security
- Disputer key security
- Voter key security

### 2. Monitoring
- False assertions must be detected
- Requires active community
- Infrastructure dependencies

### 3. Information Availability
- Voters need data access
- Complex questions
- Ambiguity in assertions

## Specific Scenario Risks

### Prediction Market Risks
- Ambiguous resolution criteria
- Early resolution requests
- Edge cases in outcomes

### Insurance Risks
- Subjective claim validity
- Large claim sizes
- Coordinated false claims

### Bridge Risks
- Cross-chain complexity
- Timing attacks
- Proof verification

---

# 20. BEST PRACTICES

## For Integrators

### Assertion Design
```
DO:
- Use clear, unambiguous language
- Specify exact resolution criteria
- Include timestamps and sources
- Define edge cases

DON'T:
- Use subjective terms
- Leave room for interpretation
- Assume implicit knowledge
- Rely on "common sense"
```

### Bond Sizing
```
Minimum Bond > Max Profit from False Assertion
                ────────────────────────────────
                Probability of Detection

Plus: Safety margin (2-3x)
Plus: DVM fees (~$1500)
```

### Liveness Selection
```
Higher Stakes → Longer Liveness
More Complex → Longer Liveness
Active Monitoring → Can be shorter
Critical Path → Longer Liveness
```

### Callback Handling
```solidity
// Always verify caller
require(msg.sender == address(oo), "Invalid caller");

// Handle all outcomes
if (assertedTruthfully) {
    // Positive path
} else {
    // Negative path (dispute succeeded)
}

// Consider dispute state
// Don't assume resolution means undisputed
```

## For Proposers

### Before Proposing
1. Verify assertion is factually correct
2. Check you have sufficient bond
3. Ensure gas for transaction
4. Understand slashing risk

### Assertion Quality
```
Good: "The Ethereum block 18000000 timestamp is 1693476575"
Bad: "Ethereum had a block around September 2023"

Good: "Biden won the 2020 US Presidential Election"
Bad: "Biden is the president"
```

## For Disputers

### When to Dispute
```
Dispute if:
P(assertion false) × Bond > Gas + Opportunity Cost

Consider:
- Evidence quality
- Community consensus
- Historical precedent
```

### Evidence Gathering
- Primary sources preferred
- Multiple independent sources
- Timestamped records
- On-chain data when possible

## For Voters

### Voting Principles
1. Vote based on available facts
2. Consider Schelling point (what others think)
3. Review provided evidence
4. Check precedent for similar votes

### Common Pitfalls
- Voting emotionally
- Ignoring contrary evidence
- Following without research
- Missing reveal phase

---

# APPENDIX A: KEY FORMULAS

## Economic Security

```
Security Budget = UMA Market Cap × 0.5 × Participation Rate

Attack Cost = Security Budget × (1 + Risk Premium)

Safe TVL ≤ Security Budget / Risk Factor
```

## Bond Calculations

```
Minimum Bond = DVM Fee + Expected Value of Dispute

Optimal Bond = Max(Minimum Bond, TVL at Risk / Safety Factor)
```

## Voting Rewards

```
Your Reward = (Your Stake / Total Correct Stake) × Reward Pool

Reward Pool = Inflation + Fees + Slashed Stakes

APY ≈ (Inflation Rate × Votes per Year) / (1 - Slash Rate × Error Rate)
```

---

# APPENDIX B: GLOSSARY

| Term | Definition |
|------|------------|
| Assertion | A claim about reality submitted to the OO |
| Bond | Collateral posted to back an assertion |
| Challenge Window | Time period for disputes (liveness) |
| DVM | Data Verification Mechanism (voting system) |
| Escalation Manager | Custom dispute handling logic |
| Final Fee | Cost paid to DVM for resolution |
| GAT | Governance Attention Threshold (min participation) |
| Liveness | Duration of challenge window |
| OO | Optimistic Oracle |
| Proposer | Entity making an assertion |
| Disputer | Entity challenging an assertion |
| Schelling Point | Focal point for coordination (truth) |
| Slash | Penalty for incorrect votes |
| UMIP | UMA Improvement Proposal |

---

# APPENDIX C: RESOURCES

## Official Resources
- Website: https://uma.xyz
- Documentation: https://docs.uma.xyz
- GitHub: https://github.com/UMAprotocol
- Discord: UMA Protocol Discord
- Forum: discourse.uma.xyz

## Contract Addresses
- See official docs for current addresses
- Different per chain
- Verify before integration

## Tools
- UMA Oracle Interface
- Voter Dashboard
- oSnap Dashboard
- Across Bridge

---

*This knowledge base represents comprehensive documentation of UMA Protocol as of the knowledge cutoff. Protocol details may evolve - always consult official documentation for current specifications.*
