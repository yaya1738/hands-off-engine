"""
Arbitrage Detection Module
==========================

Cross-platform arbitrage detection for:
- Prediction Markets (Polymarket, Kalshi)
- Sports Betting (Polymarket vs Sportsbooks)
- Crypto (CEX/DEX price discrepancies)

Zero-risk arbitrage occurs when you can lock in guaranteed profit
by taking opposite positions on different platforms.

Example: If Polymarket has "Trump wins" at 55% YES and Kalshi has
the same event at 48% YES, you can buy YES on Kalshi and NO on
Polymarket. Combined cost: 48% + 45% = 93%, guaranteed payout: 100%.
Profit: 7% risk-free.
"""

from .types import (
    Platform,
    ArbitrageOpportunity,
    PredictionMarket,
    CryptoPrice,
    MatchedEvent,
)
from .opportunity_detector import ArbitrageDetector

__all__ = [
    'Platform',
    'ArbitrageOpportunity',
    'PredictionMarket',
    'CryptoPrice',
    'MatchedEvent',
    'ArbitrageDetector',
]
