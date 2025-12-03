"""
Crypto Exchange Fetcher
=======================

Fetches price data from multiple crypto exchanges for arbitrage detection.

Supports:
- CEX: Binance, Coinbase, Kraken, Bybit, OKX
- DEX: Uniswap (via price APIs)

For real-time arbitrage, we fetch bid/ask prices to calculate
actual execution prices including spreads.
"""

import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..types import Platform, CryptoPrice

logger = logging.getLogger(__name__)


class CryptoFetcher:
    """
    Aggregated crypto price fetcher across multiple exchanges.

    Fetches real-time orderbook top-of-book for accurate arb calculation.
    """

    # Default trading pairs to monitor
    DEFAULT_PAIRS = [
        ("BTC", "USDT"),
        ("ETH", "USDT"),
        ("SOL", "USDT"),
        ("BTC", "USDC"),
        ("ETH", "USDC"),
    ]

    # Fee schedules (maker/taker in decimal)
    FEES = {
        Platform.BINANCE: (0.001, 0.001),      # 0.1%
        Platform.COINBASE: (0.004, 0.006),      # 0.4%/0.6% (standard)
        Platform.KRAKEN: (0.0016, 0.0026),      # 0.16%/0.26%
        Platform.BYBIT: (0.001, 0.001),         # 0.1%
        Platform.OKX: (0.0008, 0.001),          # 0.08%/0.1%
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'hands-off-engine/1.0',
            'Accept': 'application/json',
        })

    def fetch_all_prices(
        self,
        pairs: Optional[List[Tuple[str, str]]] = None,
        platforms: Optional[List[Platform]] = None,
    ) -> Dict[str, List[CryptoPrice]]:
        """
        Fetch prices for all pairs across all exchanges.

        Args:
            pairs: List of (base, quote) tuples. Defaults to common pairs.
            platforms: List of platforms to fetch from. Defaults to all CEX.

        Returns:
            Dict mapping pair strings to list of CryptoPrice from each exchange
        """
        if pairs is None:
            pairs = self.DEFAULT_PAIRS

        if platforms is None:
            platforms = [
                Platform.BINANCE,
                Platform.COINBASE,
                Platform.KRAKEN,
                Platform.BYBIT,
                Platform.OKX,
            ]

        results: Dict[str, List[CryptoPrice]] = {}

        # Fetch in parallel for speed
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}

            for base, quote in pairs:
                pair_key = f"{base}/{quote}"
                results[pair_key] = []

                for platform in platforms:
                    future = executor.submit(
                        self._fetch_single_price,
                        platform, base, quote
                    )
                    futures[future] = (pair_key, platform)

            for future in as_completed(futures):
                pair_key, platform = futures[future]
                try:
                    price = future.result()
                    if price:
                        results[pair_key].append(price)
                except Exception as e:
                    logger.debug(f"Failed to fetch {pair_key} from {platform}: {e}")

        return results

    def _fetch_single_price(
        self,
        platform: Platform,
        base: str,
        quote: str,
    ) -> Optional[CryptoPrice]:
        """Fetch price from a single exchange"""
        fetcher_map = {
            Platform.BINANCE: self._fetch_binance,
            Platform.COINBASE: self._fetch_coinbase,
            Platform.KRAKEN: self._fetch_kraken,
            Platform.BYBIT: self._fetch_bybit,
            Platform.OKX: self._fetch_okx,
        }

        fetcher = fetcher_map.get(platform)
        if not fetcher:
            return None

        return fetcher(base, quote)

    def _fetch_binance(self, base: str, quote: str) -> Optional[CryptoPrice]:
        """Fetch from Binance"""
        try:
            symbol = f"{base}{quote}"
            url = f"https://api.binance.com/api/v3/ticker/bookTicker"

            response = self._session.get(
                url,
                params={'symbol': symbol},
                timeout=self.timeout
            )

            if response.status_code != 200:
                return None

            data = response.json()

            bid = float(data['bidPrice'])
            ask = float(data['askPrice'])
            mid = (bid + ask) / 2

            maker_fee, taker_fee = self.FEES[Platform.BINANCE]

            return CryptoPrice(
                platform=Platform.BINANCE,
                base_asset=base,
                quote_asset=quote,
                bid_price=bid,
                ask_price=ask,
                mid_price=mid,
                bid_size=float(data.get('bidQty', 0)),
                ask_size=float(data.get('askQty', 0)),
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                fetched_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.debug(f"Binance fetch failed for {base}/{quote}: {e}")
            return None

    def _fetch_coinbase(self, base: str, quote: str) -> Optional[CryptoPrice]:
        """Fetch from Coinbase"""
        try:
            product_id = f"{base}-{quote}"
            url = f"https://api.exchange.coinbase.com/products/{product_id}/ticker"

            response = self._session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                return None

            data = response.json()

            bid = float(data['bid'])
            ask = float(data['ask'])
            mid = (bid + ask) / 2

            maker_fee, taker_fee = self.FEES[Platform.COINBASE]

            return CryptoPrice(
                platform=Platform.COINBASE,
                base_asset=base,
                quote_asset=quote,
                bid_price=bid,
                ask_price=ask,
                mid_price=mid,
                volume_24h=float(data.get('volume', 0)),
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                fetched_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.debug(f"Coinbase fetch failed for {base}/{quote}: {e}")
            return None

    def _fetch_kraken(self, base: str, quote: str) -> Optional[CryptoPrice]:
        """Fetch from Kraken"""
        try:
            # Kraken uses different ticker symbols
            kraken_base = 'XBT' if base == 'BTC' else base
            pair = f"{kraken_base}{quote}"
            url = "https://api.kraken.com/0/public/Ticker"

            response = self._session.get(
                url,
                params={'pair': pair},
                timeout=self.timeout
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if data.get('error'):
                return None

            result = data.get('result', {})
            # Kraken returns with weird key names
            ticker_data = list(result.values())[0] if result else None
            if not ticker_data:
                return None

            # 'b' is bid [price, whole_lot_volume, lot_volume]
            # 'a' is ask [price, whole_lot_volume, lot_volume]
            bid = float(ticker_data['b'][0])
            ask = float(ticker_data['a'][0])
            mid = (bid + ask) / 2

            maker_fee, taker_fee = self.FEES[Platform.KRAKEN]

            return CryptoPrice(
                platform=Platform.KRAKEN,
                base_asset=base,
                quote_asset=quote,
                bid_price=bid,
                ask_price=ask,
                mid_price=mid,
                volume_24h=float(ticker_data.get('v', [0, 0])[1]),
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                fetched_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.debug(f"Kraken fetch failed for {base}/{quote}: {e}")
            return None

    def _fetch_bybit(self, base: str, quote: str) -> Optional[CryptoPrice]:
        """Fetch from Bybit"""
        try:
            symbol = f"{base}{quote}"
            url = "https://api.bybit.com/v5/market/tickers"

            response = self._session.get(
                url,
                params={'category': 'spot', 'symbol': symbol},
                timeout=self.timeout
            )

            if response.status_code != 200:
                return None

            data = response.json()
            result_list = data.get('result', {}).get('list', [])
            if not result_list:
                return None

            ticker = result_list[0]

            bid = float(ticker['bid1Price'])
            ask = float(ticker['ask1Price'])
            mid = (bid + ask) / 2

            maker_fee, taker_fee = self.FEES[Platform.BYBIT]

            return CryptoPrice(
                platform=Platform.BYBIT,
                base_asset=base,
                quote_asset=quote,
                bid_price=bid,
                ask_price=ask,
                mid_price=mid,
                bid_size=float(ticker.get('bid1Size', 0)),
                ask_size=float(ticker.get('ask1Size', 0)),
                volume_24h=float(ticker.get('volume24h', 0)),
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                fetched_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.debug(f"Bybit fetch failed for {base}/{quote}: {e}")
            return None

    def _fetch_okx(self, base: str, quote: str) -> Optional[CryptoPrice]:
        """Fetch from OKX"""
        try:
            inst_id = f"{base}-{quote}"
            url = "https://www.okx.com/api/v5/market/ticker"

            response = self._session.get(
                url,
                params={'instId': inst_id},
                timeout=self.timeout
            )

            if response.status_code != 200:
                return None

            data = response.json()
            ticker_list = data.get('data', [])
            if not ticker_list:
                return None

            ticker = ticker_list[0]

            bid = float(ticker['bidPx'])
            ask = float(ticker['askPx'])
            mid = (bid + ask) / 2

            maker_fee, taker_fee = self.FEES[Platform.OKX]

            return CryptoPrice(
                platform=Platform.OKX,
                base_asset=base,
                quote_asset=quote,
                bid_price=bid,
                ask_price=ask,
                mid_price=mid,
                bid_size=float(ticker.get('bidSz', 0)),
                ask_size=float(ticker.get('askSz', 0)),
                volume_24h=float(ticker.get('vol24h', 0)),
                maker_fee=maker_fee,
                taker_fee=taker_fee,
                fetched_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.debug(f"OKX fetch failed for {base}/{quote}: {e}")
            return None

    def fetch_pair(
        self,
        base: str,
        quote: str,
    ) -> List[CryptoPrice]:
        """Fetch a single pair from all exchanges"""
        result = self.fetch_all_prices(
            pairs=[(base, quote)],
        )
        return result.get(f"{base}/{quote}", [])
