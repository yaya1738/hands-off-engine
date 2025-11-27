"""
Arbitrage Fetchers
==================

Data fetchers for various platforms:
- Prediction Markets: Polymarket, Kalshi
- Sports Betting: via odds APIs
- Crypto: CEX/DEX price feeds
"""

from .polymarket import PolymarketFetcher
from .kalshi import KalshiFetcher
from .crypto_exchanges import CryptoFetcher

__all__ = [
    'PolymarketFetcher',
    'KalshiFetcher',
    'CryptoFetcher',
]
