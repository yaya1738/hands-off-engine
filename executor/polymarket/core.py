"""
Polymarket Core - Foundational Knowledge and Market Structure
=============================================================

Complete understanding of Polymarket's prediction market mechanics:
- Market structure and types
- Outcome tokens (YES/NO, multi-outcome)
- Resolution mechanisms
- Fee structure
- CTF (Conditional Token Framework)
- UMA oracle integration
- Price mechanics and arbitrage constraints

POLYMARKET FUNDAMENTALS:
------------------------
- Prediction market on Polygon (MATIC) network
- Uses USDC as collateral currency
- Binary markets: YES/NO tokens sum to $1
- Multi-outcome: All outcome tokens sum to $1
- Central Limit Order Book (CLOB) for trading
- UMA optimistic oracle for resolution

USAGE:
    from executor.polymarket.core import market

    market.binary_constraint(0.65, 0.35)  # Check if valid
    market.implied_probability(0.65)       # 65%
    market.outcome_value_at_resolution(0.65, True)  # $1 if YES wins
"""

import math
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class MarketType(Enum):
    """Types of prediction markets on Polymarket"""
    BINARY = "binary"           # YES/NO
    MULTI_OUTCOME = "multi"     # Multiple mutually exclusive outcomes
    SCALAR = "scalar"           # Numeric range (rare)


class MarketStatus(Enum):
    """Market lifecycle states"""
    UPCOMING = "upcoming"       # Not yet open for trading
    ACTIVE = "active"           # Open for trading
    CLOSED = "closed"           # Trading ended, awaiting resolution
    RESOLVED = "resolved"       # Final outcome determined
    DISPUTED = "disputed"       # Resolution challenged
    EMERGENCY = "emergency"     # Emergency resolution in progress


class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order types supported by Polymarket CLOB"""
    GTC = "GTC"     # Good Till Cancelled
    GTD = "GTD"     # Good Till Date
    FOK = "FOK"     # Fill Or Kill
    IOC = "IOC"     # Immediate Or Cancel


class ResolutionSource(Enum):
    """Resolution data sources"""
    UMA_ORACLE = "uma"              # UMA optimistic oracle
    OFFICIAL_SOURCE = "official"    # Official data source
    POLYMARKET_ADMIN = "admin"      # Polymarket team decision


@dataclass
class MarketOutcome:
    """Represents a single outcome in a market"""
    token_id: str
    name: str
    price: float  # Current price (0-1)

    @property
    def implied_probability(self) -> float:
        return self.price

    @property
    def decimal_odds(self) -> float:
        return 1 / self.price if self.price > 0 else float('inf')


@dataclass
class Market:
    """Complete market representation"""
    condition_id: str
    question: str
    description: str
    market_type: MarketType
    outcomes: List[MarketOutcome]
    status: MarketStatus
    end_date: Optional[datetime]
    resolution_source: ResolutionSource
    volume: float
    liquidity: float
    created_at: datetime
    category: str
    tags: List[str]


class PolymarketCore:
    """
    Core Polymarket knowledge and calculations.

    Implements fundamental prediction market mathematics and
    Polymarket-specific mechanics.
    """

    # ==========================================
    # CONSTANTS
    # ==========================================

    # Polymarket fee structure (as of 2024)
    MAKER_FEE = 0.0      # 0% maker fee
    TAKER_FEE = 0.0      # 0% taker fee (promotional)
    RESOLUTION_FEE = 0.02  # 2% on winnings (charged at resolution)

    # Network constants
    CHAIN_ID = 137       # Polygon mainnet
    USDC_DECIMALS = 6
    COLLATERAL_TOKEN = "USDC"

    # CLOB constraints
    MIN_TICK_SIZE = 0.001   # Minimum price increment ($0.001)
    MIN_ORDER_SIZE = 0.01   # Minimum order size in USDC
    MAX_ORDER_SIZE = 100000  # Maximum single order

    # Price bounds
    MIN_PRICE = 0.001
    MAX_PRICE = 0.999

    # API endpoints
    CLOB_HOST = "https://clob.polymarket.com"
    GAMMA_HOST = "https://gamma-api.polymarket.com"

    # ==========================================
    # PRICE AND PROBABILITY
    # ==========================================

    def price_to_probability(self, price: float) -> float:
        """Convert market price to implied probability"""
        return max(0.0, min(1.0, price))

    def probability_to_price(self, prob: float) -> float:
        """Convert probability to market price"""
        return max(self.MIN_PRICE, min(self.MAX_PRICE, prob))

    def decimal_odds(self, price: float) -> float:
        """Convert price to decimal odds (e.g., 0.5 -> 2.0)"""
        if price <= 0:
            return float('inf')
        return 1.0 / price

    def american_odds(self, price: float) -> float:
        """Convert price to American odds format"""
        if price <= 0:
            return float('inf')
        if price >= 1:
            return float('-inf')

        if price >= 0.5:
            # Favorite: negative odds
            return -100 * price / (1 - price)
        else:
            # Underdog: positive odds
            return 100 * (1 - price) / price

    def fractional_odds(self, price: float) -> Tuple[int, int]:
        """Convert price to fractional odds (UK style)"""
        if price <= 0 or price >= 1:
            return (0, 0)

        decimal = self.decimal_odds(price) - 1

        # Common fractions
        fractions = [
            (1, 10), (1, 5), (2, 9), (1, 4), (2, 7), (3, 10),
            (1, 3), (4, 11), (2, 5), (4, 9), (1, 2), (8, 15),
            (4, 7), (8, 13), (4, 6), (8, 11), (4, 5), (5, 6),
            (10, 11), (1, 1), (11, 10), (6, 5), (5, 4), (11, 8),
            (6, 4), (13, 8), (7, 4), (15, 8), (2, 1), (9, 4),
            (5, 2), (11, 4), (3, 1), (7, 2), (4, 1), (9, 2),
            (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1)
        ]

        best = min(fractions, key=lambda f: abs(f[0]/f[1] - decimal))
        return best

    def implied_probability_from_odds(self, decimal_odds: float) -> float:
        """Convert decimal odds back to implied probability"""
        if decimal_odds <= 0:
            return 0.0
        return 1.0 / decimal_odds

    # ==========================================
    # BINARY MARKET MECHANICS
    # ==========================================

    def binary_constraint(self, yes_price: float, no_price: float,
                          tolerance: float = 0.01) -> bool:
        """
        Check if YES + NO prices satisfy binary constraint.
        In efficient market: YES + NO = 1
        """
        return abs(yes_price + no_price - 1.0) <= tolerance

    def no_price_from_yes(self, yes_price: float) -> float:
        """Calculate NO price from YES price"""
        return 1.0 - yes_price

    def yes_price_from_no(self, no_price: float) -> float:
        """Calculate YES price from NO price"""
        return 1.0 - no_price

    def binary_arbitrage_check(self, yes_price: float, no_price: float) -> Dict:
        """
        Check for arbitrage in binary market.

        Arbitrage exists if:
        - YES + NO < 1: Buy both, guaranteed profit
        - YES + NO > 1: Sell both (if possible), guaranteed profit
        """
        total = yes_price + no_price

        if total < 1.0 - self.MIN_TICK_SIZE:
            profit_per_dollar = 1.0 - total
            return {
                'arbitrage': True,
                'type': 'underpriced',
                'action': 'buy_both',
                'profit_per_dollar': profit_per_dollar,
                'strategy': f'Buy YES@{yes_price:.3f} and NO@{no_price:.3f}, profit ${profit_per_dollar:.3f} per $1 invested'
            }
        elif total > 1.0 + self.MIN_TICK_SIZE:
            profit_per_dollar = total - 1.0
            return {
                'arbitrage': True,
                'type': 'overpriced',
                'action': 'sell_both',
                'profit_per_dollar': profit_per_dollar,
                'strategy': f'Sell YES@{yes_price:.3f} and NO@{no_price:.3f} if holding'
            }
        else:
            return {
                'arbitrage': False,
                'type': 'efficient',
                'spread': abs(total - 1.0)
            }

    # ==========================================
    # MULTI-OUTCOME MARKET MECHANICS
    # ==========================================

    def multi_outcome_constraint(self, prices: List[float],
                                  tolerance: float = 0.02) -> bool:
        """
        Check if multi-outcome prices satisfy constraint.
        Sum of all outcome prices should equal 1.
        """
        return abs(sum(prices) - 1.0) <= tolerance

    def normalize_prices(self, prices: List[float]) -> List[float]:
        """Normalize prices to sum to 1"""
        total = sum(prices)
        if total == 0:
            return [1.0 / len(prices)] * len(prices)
        return [p / total for p in prices]

    def multi_outcome_arbitrage(self, prices: List[float]) -> Dict:
        """Check for arbitrage in multi-outcome market"""
        total = sum(prices)
        n = len(prices)

        if total < 1.0 - 0.01:
            return {
                'arbitrage': True,
                'type': 'underpriced',
                'action': 'buy_all',
                'profit_per_dollar': 1.0 - total,
                'strategy': f'Buy all {n} outcomes, guaranteed ${1.0 - total:.3f} profit'
            }
        elif total > 1.0 + 0.01:
            return {
                'arbitrage': True,
                'type': 'overpriced',
                'action': 'sell_all_or_hedge',
                'excess': total - 1.0
            }
        else:
            return {'arbitrage': False, 'type': 'efficient'}

    # ==========================================
    # POSITION VALUE CALCULATIONS
    # ==========================================

    def position_value(self, shares: float, current_price: float) -> float:
        """Current market value of position"""
        return shares * current_price

    def position_cost(self, shares: float, entry_price: float) -> float:
        """Cost basis of position"""
        return shares * entry_price

    def unrealized_pnl(self, shares: float, entry_price: float,
                       current_price: float) -> float:
        """Unrealized profit/loss"""
        return shares * (current_price - entry_price)

    def unrealized_pnl_percent(self, entry_price: float,
                               current_price: float) -> float:
        """Unrealized P&L as percentage"""
        if entry_price == 0:
            return 0.0
        return (current_price - entry_price) / entry_price * 100

    def value_at_resolution(self, shares: float, outcome_wins: bool) -> float:
        """
        Position value when market resolves.

        If outcome wins: shares * $1.00 = shares
        If outcome loses: $0.00
        """
        return shares if outcome_wins else 0.0

    def max_profit(self, shares: float, entry_price: float) -> float:
        """Maximum possible profit (if outcome wins)"""
        return shares * (1.0 - entry_price)

    def max_loss(self, shares: float, entry_price: float) -> float:
        """Maximum possible loss (if outcome loses)"""
        return shares * entry_price

    def expected_value(self, shares: float, entry_price: float,
                       true_probability: float) -> float:
        """
        Expected value of position given true probability.

        EV = P(win) * payout - P(lose) * cost
        """
        win_value = shares * 1.0 * true_probability
        lose_value = 0.0
        cost = shares * entry_price
        return win_value - cost

    def kelly_criterion(self, win_prob: float, market_price: float) -> float:
        """
        Kelly criterion for optimal bet sizing.

        f* = (bp - q) / b
        where:
        - b = decimal odds - 1 = (1/price) - 1
        - p = true probability of winning
        - q = 1 - p

        Returns fraction of bankroll to bet (0 = don't bet, negative = bet other side)
        """
        if market_price <= 0 or market_price >= 1:
            return 0.0

        b = (1.0 / market_price) - 1  # Net odds
        p = win_prob
        q = 1 - p

        kelly = (b * p - q) / b if b > 0 else 0.0
        return kelly

    def half_kelly(self, win_prob: float, market_price: float) -> float:
        """Half Kelly for more conservative sizing"""
        return self.kelly_criterion(win_prob, market_price) / 2

    # ==========================================
    # FEE CALCULATIONS
    # ==========================================

    def trading_fee(self, size: float, is_maker: bool = False) -> float:
        """Calculate trading fee"""
        fee_rate = self.MAKER_FEE if is_maker else self.TAKER_FEE
        return size * fee_rate

    def resolution_fee(self, winnings: float) -> float:
        """Calculate resolution fee on winnings"""
        return winnings * self.RESOLUTION_FEE

    def net_payout(self, shares: float, entry_price: float,
                   outcome_wins: bool) -> float:
        """Net payout after all fees"""
        if not outcome_wins:
            return 0.0

        gross_payout = shares * 1.0
        cost = shares * entry_price
        profit = gross_payout - cost

        if profit > 0:
            fee = self.resolution_fee(profit)
            return gross_payout - fee
        return gross_payout

    def break_even_price(self, entry_price: float) -> float:
        """
        Break-even market price accounting for resolution fee.
        Need price to reach this for profitable exit.
        """
        # With 2% resolution fee on profits:
        # To break even: (exit - entry) * 0.98 = 0
        # Simplifies to: exit > entry (fee only on profit)
        return entry_price  # No loss if you exit at entry

    # ==========================================
    # COLLATERAL AND SHARES
    # ==========================================

    def shares_from_collateral(self, collateral: float, price: float) -> float:
        """Calculate shares purchasable with given collateral"""
        if price <= 0:
            return 0.0
        return collateral / price

    def collateral_required(self, shares: float, price: float) -> float:
        """Calculate collateral required for given shares"""
        return shares * price

    def mint_complete_set(self, usdc_amount: float) -> Dict[str, float]:
        """
        Mint complete set of outcome tokens.

        For binary: $1 USDC -> 1 YES + 1 NO token
        Both tokens together always worth $1
        """
        return {
            'yes_tokens': usdc_amount,
            'no_tokens': usdc_amount,
            'usdc_spent': usdc_amount
        }

    def redeem_complete_set(self, yes_tokens: float, no_tokens: float) -> float:
        """
        Redeem complete set for USDC.

        1 YES + 1 NO = $1 USDC
        """
        redeemable = min(yes_tokens, no_tokens)
        return redeemable

    # ==========================================
    # CTF (CONDITIONAL TOKEN FRAMEWORK)
    # ==========================================

    def calculate_condition_id(self, oracle: str, question_id: str,
                               outcome_slot_count: int) -> str:
        """
        Calculate condition ID (simplified).

        In reality: keccak256(abi.encodePacked(oracle, questionId, outcomeSlotCount))
        """
        # Placeholder - real implementation uses keccak256
        return f"condition_{oracle[:8]}_{question_id[:8]}_{outcome_slot_count}"

    def calculate_collection_id(self, condition_id: str,
                                index_set: int) -> str:
        """
        Calculate collection ID for outcome tokens.

        index_set is a bitmap of outcomes (e.g., 1 for YES, 2 for NO in binary)
        """
        return f"collection_{condition_id[:16]}_{index_set}"

    def calculate_position_id(self, collateral_token: str,
                              collection_id: str) -> str:
        """Calculate position ID (ERC1155 token ID)"""
        return f"position_{collateral_token[:8]}_{collection_id[:16]}"

    # ==========================================
    # MARKET EFFICIENCY METRICS
    # ==========================================

    def bid_ask_spread(self, best_bid: float, best_ask: float) -> float:
        """Calculate bid-ask spread"""
        return best_ask - best_bid

    def spread_percentage(self, best_bid: float, best_ask: float) -> float:
        """Spread as percentage of mid price"""
        mid = (best_bid + best_ask) / 2
        if mid == 0:
            return 0.0
        return (best_ask - best_bid) / mid * 100

    def mid_price(self, best_bid: float, best_ask: float) -> float:
        """Calculate mid price"""
        return (best_bid + best_ask) / 2

    def effective_spread(self, trade_price: float, mid_price: float) -> float:
        """Effective spread based on execution price"""
        return 2 * abs(trade_price - mid_price)

    def market_depth_ratio(self, bid_depth: float, ask_depth: float) -> float:
        """Ratio of bid to ask depth (>1 = more buy pressure)"""
        if ask_depth == 0:
            return float('inf')
        return bid_depth / ask_depth

    def price_impact_estimate(self, order_size: float,
                              depth_at_level: float,
                              levels_to_consume: int = 1) -> float:
        """Estimate price impact of order"""
        if depth_at_level == 0:
            return 1.0  # 100% impact
        impact = (order_size / depth_at_level) * levels_to_consume * self.MIN_TICK_SIZE
        return min(impact, 1.0)

    # ==========================================
    # TIME VALUE AND DECAY
    # ==========================================

    def time_to_resolution(self, end_date: datetime) -> timedelta:
        """Time remaining until market resolution"""
        return end_date - datetime.now()

    def days_to_resolution(self, end_date: datetime) -> float:
        """Days remaining until resolution"""
        delta = self.time_to_resolution(end_date)
        return delta.total_seconds() / 86400

    def annualized_return(self, current_price: float, days_to_resolution: float,
                          win_probability: float = 1.0) -> float:
        """
        Annualized return if outcome wins.

        Useful for comparing opportunities across different time horizons.
        """
        if current_price >= 1 or days_to_resolution <= 0:
            return 0.0

        # Expected return per dollar
        expected_return = (win_probability * 1.0 - current_price) / current_price

        # Annualize
        years = days_to_resolution / 365
        if years > 0:
            annualized = (1 + expected_return) ** (1 / years) - 1
            return annualized * 100
        return expected_return * 100

    def time_decay_factor(self, days_remaining: float,
                          total_days: float) -> float:
        """
        Time decay factor for position.

        As resolution approaches, uncertainty decreases.
        Price should converge to 0 or 1.
        """
        if total_days <= 0:
            return 0.0
        return days_remaining / total_days

    # ==========================================
    # RESOLUTION MECHANICS
    # ==========================================

    def uma_bond_requirement(self, dispute_level: int = 0) -> float:
        """
        UMA oracle bond requirement.

        Increases with each dispute level.
        """
        base_bond = 750  # Base bond in USDC
        return base_bond * (2 ** dispute_level)

    def uma_dispute_window(self) -> timedelta:
        """Standard UMA dispute window"""
        return timedelta(hours=2)  # 2 hour challenge period

    def resolution_timeline(self, market_close: datetime) -> Dict[str, datetime]:
        """Expected resolution timeline after market closes"""
        return {
            'market_closes': market_close,
            'initial_assertion': market_close + timedelta(hours=1),
            'dispute_window_end': market_close + timedelta(hours=3),
            'earliest_resolution': market_close + timedelta(hours=3),
            'typical_resolution': market_close + timedelta(hours=24)
        }

    # ==========================================
    # MARKET CATEGORIES
    # ==========================================

    CATEGORIES = {
        'politics': {
            'description': 'Elections, legislation, political events',
            'subcategories': ['US Politics', 'International', 'Policy'],
            'typical_resolution': 'Official results or announcements',
            'volatility': 'Medium-High',
            'liquidity': 'High'
        },
        'sports': {
            'description': 'Sports outcomes and championships',
            'subcategories': ['NFL', 'NBA', 'Soccer', 'UFC', 'Olympics'],
            'typical_resolution': 'Official game/match results',
            'volatility': 'Medium',
            'liquidity': 'High during events'
        },
        'crypto': {
            'description': 'Cryptocurrency prices and events',
            'subcategories': ['Bitcoin', 'Ethereum', 'Altcoins', 'DeFi'],
            'typical_resolution': 'Price feeds (Chainlink/others)',
            'volatility': 'Very High',
            'liquidity': 'Medium-High'
        },
        'entertainment': {
            'description': 'Awards, releases, celebrity events',
            'subcategories': ['Awards', 'Box Office', 'TV', 'Music'],
            'typical_resolution': 'Official announcements',
            'volatility': 'Low-Medium',
            'liquidity': 'Low-Medium'
        },
        'science': {
            'description': 'Scientific discoveries and events',
            'subcategories': ['Space', 'Climate', 'Technology'],
            'typical_resolution': 'Official reports/NASA/agencies',
            'volatility': 'Low',
            'liquidity': 'Low'
        },
        'finance': {
            'description': 'Economic indicators and financial events',
            'subcategories': ['Fed', 'Markets', 'Economic Data'],
            'typical_resolution': 'Official government/Fed releases',
            'volatility': 'Medium',
            'liquidity': 'Medium-High'
        }
    }

    def get_category_info(self, category: str) -> Optional[Dict]:
        """Get information about a market category"""
        return self.CATEGORIES.get(category.lower())

    def list_categories(self) -> List[str]:
        """List all market categories"""
        return list(self.CATEGORIES.keys())


# Singleton instance
market = PolymarketCore()
