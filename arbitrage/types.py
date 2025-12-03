"""
Arbitrage Type Definitions
==========================

Core data types for cross-platform arbitrage detection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class Platform(Enum):
    """Supported trading platforms"""
    # Prediction Markets
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"

    # Sports Betting
    DRAFTKINGS = "draftkings"
    FANDUEL = "fanduel"
    BETMGM = "betmgm"
    PINNACLE = "pinnacle"

    # Crypto Exchanges (CEX)
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKX = "okx"

    # Crypto DEX
    UNISWAP = "uniswap"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"

    # Special
    COMPOSITE = "composite"  # For aggregated/matched events


class ArbitrageType(Enum):
    """Types of arbitrage opportunities"""
    # Prediction market arbitrage
    TWO_WAY_BINARY = "two_way_binary"       # YES/NO on same event, different platforms
    THREE_WAY = "three_way"                  # Sports with draw option
    MULTI_OUTCOME = "multi_outcome"          # Multiple outcomes (e.g., who wins election)

    # Crypto arbitrage
    SIMPLE_SPOT = "simple_spot"              # Buy on exchange A, sell on exchange B
    TRIANGULAR = "triangular"                # A→B→C→A within same exchange
    CROSS_CHAIN = "cross_chain"              # Same asset, different chains
    CEX_DEX = "cex_dex"                       # Centralized vs decentralized


@dataclass
class PredictionMarket:
    """A prediction market on any platform"""
    platform: Platform
    market_id: str
    question: str

    # Binary market prices (0.0 to 1.0)
    yes_price: float
    no_price: float

    # Optional: for multi-outcome markets
    outcomes: Optional[Dict[str, float]] = None  # outcome_name -> price

    # Liquidity and metadata
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    best_bid_yes: Optional[float] = None
    best_ask_yes: Optional[float] = None
    best_bid_no: Optional[float] = None
    best_ask_no: Optional[float] = None

    # Timing
    closes_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None

    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = field(default=None, repr=False)

    @property
    def spread(self) -> float:
        """Market spread (overround). 1.0 = fair, >1.0 = has vig"""
        return self.yes_price + self.no_price

    @property
    def implied_vig(self) -> float:
        """Implied vig/juice (how much over 100%)"""
        return max(0, self.spread - 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'platform': self.platform.value,
            'market_id': self.market_id,
            'question': self.question,
            'yes_price': self.yes_price,
            'no_price': self.no_price,
            'spread': self.spread,
            'volume_24h': self.volume_24h,
            'liquidity': self.liquidity,
            'closes_at': self.closes_at.isoformat() if self.closes_at else None,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
        }


@dataclass
class CryptoPrice:
    """Price quote for a crypto asset on an exchange"""
    platform: Platform
    base_asset: str         # e.g., "BTC"
    quote_asset: str        # e.g., "USDT"

    # Prices
    bid_price: float        # Best bid (what you get when selling)
    ask_price: float        # Best ask (what you pay when buying)
    mid_price: float        # Midpoint

    # Volume and liquidity
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    volume_24h: Optional[float] = None

    # Timing
    fetched_at: Optional[datetime] = None

    # Fees (important for arb calculation)
    maker_fee: float = 0.001   # 0.1% default
    taker_fee: float = 0.001   # 0.1% default
    withdrawal_fee: Optional[float] = None

    @property
    def spread_pct(self) -> float:
        """Bid-ask spread as percentage"""
        if self.mid_price == 0:
            return 0
        return (self.ask_price - self.bid_price) / self.mid_price

    @property
    def pair(self) -> str:
        return f"{self.base_asset}/{self.quote_asset}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'platform': self.platform.value,
            'pair': self.pair,
            'bid_price': self.bid_price,
            'ask_price': self.ask_price,
            'mid_price': self.mid_price,
            'spread_pct': self.spread_pct,
            'volume_24h': self.volume_24h,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
        }


@dataclass
class MatchedEvent:
    """Same event matched across multiple platforms"""
    event_id: str                           # Our canonical ID
    canonical_question: str                 # Normalized question text

    markets: List[PredictionMarket]         # All platforms offering this event

    # Matching metadata
    match_confidence: float = 1.0           # How confident we are it's the same event
    match_method: str = "exact"             # How we matched: exact, fuzzy, manual

    # Category hints for matching
    category: Optional[str] = None          # sports, politics, crypto, etc.
    subcategory: Optional[str] = None       # nfl, presidential, btc_price, etc.

    created_at: Optional[datetime] = None

    def get_by_platform(self, platform: Platform) -> Optional[PredictionMarket]:
        """Get the market for a specific platform"""
        for m in self.markets:
            if m.platform == platform:
                return m
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'canonical_question': self.canonical_question,
            'match_confidence': self.match_confidence,
            'match_method': self.match_method,
            'category': self.category,
            'platforms': [m.platform.value for m in self.markets],
            'markets': [m.to_dict() for m in self.markets],
        }


@dataclass
class ArbitrageOpportunity:
    """A detected arbitrage opportunity"""
    opportunity_id: str
    arb_type: ArbitrageType

    # Profit metrics
    profit_pct: float           # Guaranteed profit percentage (before fees)
    profit_pct_net: float       # After estimated fees

    # For prediction market arb
    matched_event: Optional[MatchedEvent] = None

    # Leg details: what to buy/sell on each platform
    legs: List[Dict[str, Any]] = field(default_factory=list)
    # Each leg: {platform, side, price, size_pct, fees_est}

    # For crypto arb
    crypto_prices: Optional[List[CryptoPrice]] = None

    # Risk assessment
    execution_risk: str = "low"     # low, medium, high
    risk_factors: List[str] = field(default_factory=list)

    # Sizing
    max_size_usd: Optional[float] = None   # Limited by liquidity
    recommended_size_usd: Optional[float] = None

    # Timing
    detected_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None   # When opportunity likely closes

    # Status tracking
    status: str = "open"            # open, stale, executed, expired

    def to_dict(self) -> Dict[str, Any]:
        return {
            'opportunity_id': self.opportunity_id,
            'arb_type': self.arb_type.value,
            'profit_pct': round(self.profit_pct, 4),
            'profit_pct_net': round(self.profit_pct_net, 4),
            'legs': self.legs,
            'execution_risk': self.execution_risk,
            'risk_factors': self.risk_factors,
            'max_size_usd': self.max_size_usd,
            'recommended_size_usd': self.recommended_size_usd,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'status': self.status,
            'matched_event': self.matched_event.to_dict() if self.matched_event else None,
        }

    def summary(self) -> str:
        """Human-readable summary"""
        if self.matched_event:
            return (
                f"[{self.profit_pct_net:+.2%} NET] {self.matched_event.canonical_question[:60]}... "
                f"({len(self.legs)} legs, {self.execution_risk} risk)"
            )
        return f"[{self.profit_pct_net:+.2%} NET] {self.arb_type.value} opportunity"
