"""
UMA Protocol Knowledge Base
===========================

Comprehensive UMA oracle and dispute resolution knowledge.

KNOWLEDGE FILES:
----------------
- KNOWLEDGE.md: Complete UMA protocol reference
- KNOWLEDGE_ADVANCED.md: Deep technical internals

TOPICS COVERED:
---------------
1. Protocol Overview - What UMA is and core philosophy
2. Core Architecture - OO + DVM two-layer system
3. Optimistic Oracle - Assertions, bonds, liveness
4. Data Verification Mechanism - Token holder voting
5. Price Identifiers - UMIP process, identifier types
6. Economic Security - Attack cost analysis
7. UMA Token - Utility, staking, rewards
8. Smart Contracts - Architecture, addresses
9. Dispute Resolution - Full flow, edge cases
10. Financial Products - LSP, KPI options, etc.
11. oSnap - Optimistic governance execution
12. Oval - MEV protection for oracles
13. Integration Patterns - How to use UMA
14. Security Model - Trust assumptions, attacks
15. Governance - UMIPs, voting, upgrades
16. Historical Evolution - Timeline, milestones
17. Ecosystem - Major integrations
18. Oracle Comparisons - vs Chainlink, Pyth, etc.
19. Risk Factors - Protocol, market, operational
20. Best Practices - For integrators, proposers, voters

ADVANCED TOPICS:
----------------
- DVM cryptographic internals
- Commit-reveal scheme mathematics
- Schelling point game theory
- Economic attack analysis
- OO v3 contract architecture
- Escalation manager framework
- Cross-chain oracle mechanics
- Bond optimization formulas
- Voting reward mechanics
- Price identifier internals
- Contract upgrade patterns
- Gas optimization techniques
- Edge cases & failure modes
- MEV & front-running analysis
- Formal security properties
- Integration attack surfaces
- Historical disputes analysis
- Advanced voting strategies
- Liquidity & market dynamics

KEY CONCEPTS:
-------------
- Optimistic Oracle: Assert → Challenge → Settlement
- DVM: Decentralized voting for disputes
- Schelling Point: Coordination on truth
- Bonds: Economic security through collateral
- Liveness: Challenge window duration
- UMIP: UMA Improvement Proposal process

NETWORK INFO:
-------------
- Primary: Ethereum Mainnet
- Supported: Polygon, Arbitrum, Optimism, others
- Token: UMA (ERC-20)
- Voting: Commit-reveal scheme

API ENDPOINTS:
--------------
- Docs: https://docs.uma.xyz
- GitHub: https://github.com/UMAprotocol

USAGE:
------
This module is knowledge-only. For implementation,
see the UMA documentation and SDK.

```python
# Read the knowledge
from executor.uma import KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH

# Or import constants
from executor.uma import (
    OO_V3_ADDRESS,
    DVM_ADDRESS,
    STORE_ADDRESS,
    DEFAULT_LIVENESS,
    MIN_BOND_USD,
)
```
"""

import os

# Knowledge file paths
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE.md")
KNOWLEDGE_ADVANCED_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE_ADVANCED.md")

# ===========================================
# NETWORK CONSTANTS
# ===========================================

# Chain IDs
ETHEREUM_MAINNET = 1
POLYGON = 137
ARBITRUM = 42161
OPTIMISM = 10

# ===========================================
# CONTRACT ADDRESSES (Ethereum Mainnet)
# ===========================================

OO_V3_ADDRESS = "0xfb55F43fB9F48F63f9269DB7Dde3BbBe1ebDC0dE"
DVM_ADDRESS = "0x004395edb43EFca9885CEdad51EC9fAf93Bd34ac"
STORE_ADDRESS = "0x54f44eA3D2e7aA0ac089c4d8F7C93C27844057BF"
IDENTIFIER_WHITELIST = "0xcF649d9Da4D1362C4DAEa67573430Bd6f945e570"
FINDER_ADDRESS = "0x40f941E48A552bF496B154Af6bf55725f18D77c3"
COLLATERAL_WHITELIST = "0xdBF90434dF0B98219f87d112F37d74B1D90758c7"

# ===========================================
# PROTOCOL CONSTANTS
# ===========================================

# Default liveness period (seconds)
DEFAULT_LIVENESS = 7200  # 2 hours

# Minimum bond (approximate USD equivalent)
MIN_BOND_USD = 1500

# DVM voting periods (seconds)
COMMIT_PERIOD = 86400  # 24 hours
REVEAL_PERIOD = 86400  # 24 hours

# GAT - Governance Attention Threshold
GAT_PERCENT = 5  # 5% minimum participation

# Inflation per vote
INFLATION_PER_VOTE = 0.0005  # 0.05%

# ===========================================
# PRICE IDENTIFIERS
# ===========================================

# Common identifiers
IDENTIFIERS = {
    "YES_OR_NO_QUERY": "Binary outcomes (0, 0.5, 1)",
    "ASSERT_TRUTH": "General assertions (true/false)",
    "SHERLOCK_CLAIM": "Audit claim verification",
    "ACROSS_V2": "Cross-chain bridge verification",
    "ETH_USD": "Ethereum price in USD",
    "BTC_USD": "Bitcoin price in USD",
}

# Resolution values for YES_OR_NO_QUERY
YES = 1e18
NO = 0
UNKNOWN = 0.5e18

# ===========================================
# BOND CURRENCIES
# ===========================================

# Common bond currencies (Ethereum)
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_knowledge() -> str:
    """Read the main knowledge document."""
    with open(KNOWLEDGE_PATH, 'r') as f:
        return f.read()

def get_advanced_knowledge() -> str:
    """Read the advanced knowledge document."""
    with open(KNOWLEDGE_ADVANCED_PATH, 'r') as f:
        return f.read()

def calculate_bond_minimum(value_at_risk: float, safety_factor: float = 2.0) -> float:
    """
    Calculate recommended minimum bond for an assertion.

    Args:
        value_at_risk: Maximum value that could be stolen/lost
        safety_factor: Multiplier for safety margin (default 2x)

    Returns:
        Recommended minimum bond in USD
    """
    base_bond = value_at_risk * 0.02  # 2% of value at risk
    recommended = base_bond * safety_factor
    return max(recommended, MIN_BOND_USD)

def calculate_liveness(
    complexity: str = "medium",
    value_at_risk: float = 0,
    monitoring_quality: str = "good"
) -> int:
    """
    Calculate recommended liveness period.

    Args:
        complexity: "low", "medium", "high"
        value_at_risk: USD value at risk
        monitoring_quality: "excellent", "good", "poor"

    Returns:
        Recommended liveness in seconds
    """
    # Base liveness by complexity
    base = {
        "low": 3600,      # 1 hour
        "medium": 7200,   # 2 hours
        "high": 86400,    # 24 hours
    }.get(complexity, 7200)

    # Adjust for value at risk
    if value_at_risk > 1_000_000:
        base *= 2
    elif value_at_risk > 100_000:
        base *= 1.5

    # Adjust for monitoring quality
    monitoring_factor = {
        "excellent": 0.75,
        "good": 1.0,
        "poor": 2.0,
    }.get(monitoring_quality, 1.0)

    return int(base * monitoring_factor)

def estimate_dispute_cost(bond: float, gas_price_gwei: float = 30) -> dict:
    """
    Estimate total cost to file a dispute.

    Args:
        bond: Bond amount in USD
        gas_price_gwei: Current gas price

    Returns:
        Cost breakdown dictionary
    """
    # Gas estimates
    dispute_gas = 200_000
    eth_price = 2000  # Approximate

    gas_cost_usd = (dispute_gas * gas_price_gwei * 1e-9) * eth_price

    return {
        "bond": bond,
        "gas_cost_usd": gas_cost_usd,
        "total_cost": bond + gas_cost_usd,
        "potential_reward": bond * 2,  # Win both bonds
        "break_even_probability": (bond + gas_cost_usd) / (bond * 2),
    }

def estimate_voting_reward(
    stake: float,
    total_correct_stake: float,
    reward_pool: float
) -> float:
    """
    Estimate voting reward for correct vote.

    Args:
        stake: Your staked amount
        total_correct_stake: Total stake that voted correctly
        reward_pool: Total rewards available

    Returns:
        Your expected reward
    """
    if total_correct_stake == 0:
        return 0
    return (stake / total_correct_stake) * reward_pool

# ===========================================
# EXPORTS
# ===========================================

__all__ = [
    # Paths
    "KNOWLEDGE_PATH",
    "KNOWLEDGE_ADVANCED_PATH",

    # Network constants
    "ETHEREUM_MAINNET",
    "POLYGON",
    "ARBITRUM",
    "OPTIMISM",

    # Contract addresses
    "OO_V3_ADDRESS",
    "DVM_ADDRESS",
    "STORE_ADDRESS",
    "IDENTIFIER_WHITELIST",
    "FINDER_ADDRESS",
    "COLLATERAL_WHITELIST",

    # Protocol constants
    "DEFAULT_LIVENESS",
    "MIN_BOND_USD",
    "COMMIT_PERIOD",
    "REVEAL_PERIOD",
    "GAT_PERCENT",
    "INFLATION_PER_VOTE",

    # Identifiers
    "IDENTIFIERS",
    "YES",
    "NO",
    "UNKNOWN",

    # Currency addresses
    "USDC_ADDRESS",
    "WETH_ADDRESS",

    # Functions
    "get_knowledge",
    "get_advanced_knowledge",
    "calculate_bond_minimum",
    "calculate_liveness",
    "estimate_dispute_cost",
    "estimate_voting_reward",
]
