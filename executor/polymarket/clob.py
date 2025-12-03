"""
Polymarket CLOB (Central Limit Order Book) API
==============================================

Complete coverage of Polymarket's CLOB API including:
- Order book operations
- Order submission and management
- Market data retrieval
- Trade history
- API authentication (CLOB credentials)
- Signature generation (EIP-712)

API ENDPOINTS:
--------------
Base URL: https://clob.polymarket.com

Authentication:
- API Key derived from wallet signature
- EIP-712 typed data signing for orders
- Timestamps for replay protection

Rate Limits:
- 100 requests per 10 seconds per IP
- 10 orders per second per address

USAGE:
    from executor.polymarket.clob import clob

    # Market data
    clob.get_orderbook('token_id')
    clob.get_markets()

    # Order building
    order = clob.build_order(token_id, side, price, size)

    # Order analysis
    clob.estimate_fill(orderbook, 'BUY', 100)
"""

import time
import hashlib
import hmac
import json
import math
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    GTC = "GTC"   # Good Till Cancelled
    GTD = "GTD"   # Good Till Date
    FOK = "FOK"   # Fill Or Kill
    IOC = "IOC"   # Immediate Or Cancel


class OrderStatus(Enum):
    LIVE = "LIVE"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass
class OrderBookLevel:
    """Single price level in order book"""
    price: float
    size: float

    @property
    def value(self) -> float:
        return self.price * self.size


@dataclass
class OrderBook:
    """Complete order book snapshot"""
    token_id: str
    bids: List[OrderBookLevel]  # Sorted descending (best first)
    asks: List[OrderBookLevel]  # Sorted ascending (best first)
    timestamp: float
    hash: str = ""

    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None

    @property
    def mid_price(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def bid_depth(self) -> float:
        return sum(level.size for level in self.bids)

    @property
    def ask_depth(self) -> float:
        return sum(level.size for level in self.asks)


@dataclass
class Order:
    """Order representation"""
    order_id: str
    token_id: str
    side: Side
    price: float
    size: float
    order_type: OrderType
    status: OrderStatus
    created_at: datetime
    expiration: Optional[datetime] = None
    filled_size: float = 0.0
    maker_address: str = ""
    signature: str = ""

    @property
    def remaining_size(self) -> float:
        return self.size - self.filled_size

    @property
    def is_filled(self) -> bool:
        return self.filled_size >= self.size

    @property
    def fill_percentage(self) -> float:
        return (self.filled_size / self.size * 100) if self.size > 0 else 0


@dataclass
class Trade:
    """Trade/fill representation"""
    trade_id: str
    token_id: str
    side: Side
    price: float
    size: float
    timestamp: datetime
    maker_order_id: str
    taker_order_id: str
    maker_address: str
    taker_address: str
    fee: float = 0.0


class PolymarketCLOB:
    """
    Polymarket CLOB API wrapper and utilities.

    Provides all CLOB operations without external dependencies.
    Can be used standalone for calculations or with py_clob_client.
    """

    # API Constants
    HOST = "https://clob.polymarket.com"
    GAMMA_HOST = "https://gamma-api.polymarket.com"
    CHAIN_ID = 137  # Polygon

    # Order constraints
    MIN_TICK_SIZE = 0.001
    MIN_ORDER_SIZE = 0.01
    MAX_ORDER_SIZE = 100000
    MIN_PRICE = 0.001
    MAX_PRICE = 0.999

    # Rate limits
    REQUESTS_PER_10_SEC = 100
    ORDERS_PER_SECOND = 10

    # ==========================================
    # API ENDPOINTS REFERENCE
    # ==========================================

    ENDPOINTS = {
        # Public endpoints (no auth)
        'markets': '/markets',
        'market': '/markets/{condition_id}',
        'orderbook': '/book',
        'price': '/price',
        'spread': '/spread',
        'midpoint': '/midpoint',
        'trades': '/trades',
        'last_trade_price': '/last-trade-price',

        # Authenticated endpoints
        'orders': '/orders',
        'order': '/order/{order_id}',
        'cancel': '/order/{order_id}',
        'cancel_all': '/cancel-all',
        'cancel_market_orders': '/cancel-market-orders',
        'balances': '/balances',
        'positions': '/positions',
        'trade_history': '/trade-history',

        # API key management
        'derive_api_key': '/auth/derive-api-key',
        'create_api_key': '/auth/api-key',
        'delete_api_key': '/auth/api-key',
        'api_keys': '/auth/api-keys',

        # Gamma API endpoints
        'gamma_markets': '/markets',
        'gamma_events': '/events',
    }

    # ==========================================
    # ORDER BOOK OPERATIONS
    # ==========================================

    def parse_orderbook(self, data: Dict) -> OrderBook:
        """Parse raw orderbook data into OrderBook object"""
        bids = [OrderBookLevel(float(b['price']), float(b['size']))
                for b in data.get('bids', [])]
        asks = [OrderBookLevel(float(a['price']), float(a['size']))
                for a in data.get('asks', [])]

        # Sort bids descending, asks ascending
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        return OrderBook(
            token_id=data.get('asset_id', data.get('token_id', '')),
            bids=bids,
            asks=asks,
            timestamp=data.get('timestamp', time.time()),
            hash=data.get('hash', '')
        )

    def aggregate_depth(self, levels: List[OrderBookLevel],
                        num_levels: int = 10) -> List[Dict]:
        """Aggregate order book depth to specified levels"""
        result = []
        for i, level in enumerate(levels[:num_levels]):
            cumulative_size = sum(l.size for l in levels[:i+1])
            cumulative_value = sum(l.value for l in levels[:i+1])
            result.append({
                'price': level.price,
                'size': level.size,
                'cumulative_size': cumulative_size,
                'cumulative_value': cumulative_value,
                'level': i + 1
            })
        return result

    def depth_at_price(self, orderbook: OrderBook, price: float,
                       side: str) -> float:
        """Get total depth available at or better than price"""
        levels = orderbook.bids if side == 'BUY' else orderbook.asks

        if side == 'BUY':
            # For buy, better means lower ask prices
            return sum(l.size for l in levels if l.price <= price)
        else:
            # For sell, better means higher bid prices
            return sum(l.size for l in levels if l.price >= price)

    def depth_within_spread(self, orderbook: OrderBook,
                            spread_bps: float) -> Dict:
        """Get depth within specified spread from mid"""
        mid = orderbook.mid_price
        if not mid:
            return {'bid_depth': 0, 'ask_depth': 0}

        spread_factor = spread_bps / 10000
        bid_threshold = mid * (1 - spread_factor)
        ask_threshold = mid * (1 + spread_factor)

        bid_depth = sum(l.size for l in orderbook.bids if l.price >= bid_threshold)
        ask_depth = sum(l.size for l in orderbook.asks if l.price <= ask_threshold)

        return {
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'total_depth': bid_depth + ask_depth,
            'mid_price': mid,
            'spread_bps': spread_bps
        }

    # ==========================================
    # ORDER BUILDING
    # ==========================================

    def build_order_params(self, token_id: str, side: str, price: float,
                           size: float, order_type: str = "GTC",
                           expiration: Optional[int] = None) -> Dict:
        """Build order parameters for CLOB API"""
        # Validate inputs
        price = self.round_price(price)
        size = self.round_size(size)

        if not self.validate_price(price):
            raise ValueError(f"Invalid price: {price}")
        if not self.validate_size(size):
            raise ValueError(f"Invalid size: {size}")

        params = {
            'tokenID': token_id,
            'side': side.upper(),
            'price': str(price),
            'size': str(size),
            'type': order_type.upper()
        }

        if order_type == "GTD" and expiration:
            params['expiration'] = expiration

        return params

    def round_price(self, price: float) -> float:
        """Round price to valid tick size"""
        return round(price / self.MIN_TICK_SIZE) * self.MIN_TICK_SIZE

    def round_size(self, size: float) -> float:
        """Round size to valid precision"""
        return round(size, 2)

    def validate_price(self, price: float) -> bool:
        """Validate price is within bounds"""
        return self.MIN_PRICE <= price <= self.MAX_PRICE

    def validate_size(self, size: float) -> bool:
        """Validate order size"""
        return self.MIN_ORDER_SIZE <= size <= self.MAX_ORDER_SIZE

    def validate_order(self, price: float, size: float) -> Dict:
        """Comprehensive order validation"""
        errors = []
        warnings = []

        if price < self.MIN_PRICE:
            errors.append(f"Price {price} below minimum {self.MIN_PRICE}")
        if price > self.MAX_PRICE:
            errors.append(f"Price {price} above maximum {self.MAX_PRICE}")
        if size < self.MIN_ORDER_SIZE:
            errors.append(f"Size {size} below minimum {self.MIN_ORDER_SIZE}")
        if size > self.MAX_ORDER_SIZE:
            errors.append(f"Size {size} above maximum {self.MAX_ORDER_SIZE}")

        # Warnings
        if size > 10000:
            warnings.append("Large order may impact market price")
        if price < 0.05 or price > 0.95:
            warnings.append("Extreme price - verify before submitting")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    # ==========================================
    # FILL ESTIMATION
    # ==========================================

    def estimate_fill(self, orderbook: OrderBook, side: str,
                      size: float) -> Dict:
        """
        Estimate order fill based on current orderbook.

        Returns expected fill details including:
        - Average price
        - Total cost
        - Levels consumed
        - Price impact
        """
        levels = orderbook.asks if side == 'BUY' else orderbook.bids
        remaining = size
        total_cost = 0.0
        filled_size = 0.0
        levels_consumed = 0
        fills = []

        for level in levels:
            if remaining <= 0:
                break

            fill_at_level = min(remaining, level.size)
            cost_at_level = fill_at_level * level.price

            fills.append({
                'price': level.price,
                'size': fill_at_level,
                'cost': cost_at_level
            })

            total_cost += cost_at_level
            filled_size += fill_at_level
            remaining -= fill_at_level
            levels_consumed += 1

        avg_price = total_cost / filled_size if filled_size > 0 else 0
        best_price = levels[0].price if levels else 0

        # Calculate slippage from best price
        if best_price > 0:
            if side == 'BUY':
                slippage = (avg_price - best_price) / best_price * 100
            else:
                slippage = (best_price - avg_price) / best_price * 100
        else:
            slippage = 0

        return {
            'requested_size': size,
            'filled_size': filled_size,
            'unfilled_size': remaining,
            'fully_filled': remaining <= 0,
            'average_price': avg_price,
            'total_cost': total_cost,
            'best_price': best_price,
            'worst_price': fills[-1]['price'] if fills else 0,
            'levels_consumed': levels_consumed,
            'slippage_percent': slippage,
            'fills': fills
        }

    def estimate_market_impact(self, orderbook: OrderBook, side: str,
                               size: float) -> Dict:
        """
        Estimate market impact of an order.

        Includes:
        - Immediate impact (price move)
        - Temporary impact (expected reversion)
        - Permanent impact (lasting effect)
        """
        fill = self.estimate_fill(orderbook, side, size)

        mid_before = orderbook.mid_price or 0
        immediate_impact = abs(fill['average_price'] - mid_before) / mid_before * 100 if mid_before > 0 else 0

        # Estimate temporary vs permanent (simplified model)
        # Larger orders have more permanent impact
        depth = orderbook.bid_depth + orderbook.ask_depth
        size_ratio = size / depth if depth > 0 else 1

        temporary_ratio = max(0.3, 1 - size_ratio)  # At least 30% temporary
        permanent_ratio = min(0.7, size_ratio)       # At most 70% permanent

        return {
            **fill,
            'mid_price_before': mid_before,
            'immediate_impact_percent': immediate_impact,
            'temporary_impact_percent': immediate_impact * temporary_ratio,
            'permanent_impact_percent': immediate_impact * permanent_ratio,
            'size_to_depth_ratio': size_ratio
        }

    # ==========================================
    # PRICE CALCULATIONS
    # ==========================================

    def implied_odds(self, price: float) -> Dict:
        """Calculate implied odds from price"""
        if price <= 0 or price >= 1:
            return {'error': 'Invalid price'}

        decimal_odds = 1 / price
        american = -100 * price / (1 - price) if price >= 0.5 else 100 * (1 - price) / price

        return {
            'price': price,
            'implied_probability': price * 100,
            'decimal_odds': decimal_odds,
            'american_odds': american,
            'expected_return': (1 / price - 1) * 100
        }

    def price_from_implied_prob(self, prob: float) -> float:
        """Convert implied probability to price"""
        return max(self.MIN_PRICE, min(self.MAX_PRICE, prob))

    def calculate_spread_metrics(self, orderbook: OrderBook) -> Dict:
        """Calculate various spread metrics"""
        if not orderbook.best_bid or not orderbook.best_ask:
            return {'error': 'Incomplete orderbook'}

        bid = orderbook.best_bid
        ask = orderbook.best_ask
        mid = orderbook.mid_price

        absolute_spread = ask - bid
        relative_spread = absolute_spread / mid * 100 if mid else 0
        spread_bps = relative_spread * 100

        # Effective spreads (using depth-weighted average)
        bid_weighted = sum(l.price * l.size for l in orderbook.bids[:5])
        bid_size = sum(l.size for l in orderbook.bids[:5])
        ask_weighted = sum(l.price * l.size for l in orderbook.asks[:5])
        ask_size = sum(l.size for l in orderbook.asks[:5])

        vwap_bid = bid_weighted / bid_size if bid_size > 0 else bid
        vwap_ask = ask_weighted / ask_size if ask_size > 0 else ask

        return {
            'best_bid': bid,
            'best_ask': ask,
            'mid_price': mid,
            'absolute_spread': absolute_spread,
            'relative_spread_percent': relative_spread,
            'spread_bps': spread_bps,
            'vwap_bid_5': vwap_bid,
            'vwap_ask_5': vwap_ask,
            'effective_spread': vwap_ask - vwap_bid,
            'bid_depth_5': bid_size,
            'ask_depth_5': ask_size
        }

    # ==========================================
    # ORDER BOOK ANALYSIS
    # ==========================================

    def order_book_imbalance(self, orderbook: OrderBook,
                             levels: int = 5) -> Dict:
        """
        Calculate order book imbalance.

        Imbalance > 0: More buy pressure
        Imbalance < 0: More sell pressure
        """
        bid_size = sum(l.size for l in orderbook.bids[:levels])
        ask_size = sum(l.size for l in orderbook.asks[:levels])
        total = bid_size + ask_size

        if total == 0:
            imbalance = 0
        else:
            imbalance = (bid_size - ask_size) / total

        return {
            'bid_size': bid_size,
            'ask_size': ask_size,
            'imbalance': imbalance,  # -1 to 1
            'imbalance_percent': imbalance * 100,
            'bid_dominance': bid_size / total * 100 if total > 0 else 50,
            'interpretation': 'bullish' if imbalance > 0.1 else 'bearish' if imbalance < -0.1 else 'neutral'
        }

    def micro_price(self, orderbook: OrderBook) -> float:
        """
        Calculate micro price (volume-weighted mid).

        Better estimate of fair value than simple mid.
        """
        if not orderbook.best_bid or not orderbook.best_ask:
            return 0.0

        bid = orderbook.bids[0]
        ask = orderbook.asks[0]

        total_size = bid.size + ask.size
        if total_size == 0:
            return (bid.price + ask.price) / 2

        # Weight prices by opposing side's size
        # More ask depth -> price closer to bid
        micro = (bid.price * ask.size + ask.price * bid.size) / total_size
        return micro

    def weighted_mid_price(self, orderbook: OrderBook,
                           levels: int = 3) -> float:
        """Calculate depth-weighted mid price"""
        bid_value = sum(l.price * l.size for l in orderbook.bids[:levels])
        bid_size = sum(l.size for l in orderbook.bids[:levels])
        ask_value = sum(l.price * l.size for l in orderbook.asks[:levels])
        ask_size = sum(l.size for l in orderbook.asks[:levels])

        total_size = bid_size + ask_size
        if total_size == 0:
            return orderbook.mid_price or 0

        return (bid_value + ask_value) / total_size

    def quote_stuffing_detection(self, orderbook: OrderBook,
                                 thin_level_threshold: float = 0.1) -> Dict:
        """
        Detect potential quote stuffing or thin liquidity.

        Thin levels that could be easily consumed indicate
        possible manipulation or illiquid market.
        """
        thin_bids = sum(1 for l in orderbook.bids if l.size < thin_level_threshold)
        thin_asks = sum(1 for l in orderbook.asks if l.size < thin_level_threshold)

        return {
            'thin_bid_levels': thin_bids,
            'thin_ask_levels': thin_asks,
            'total_levels': len(orderbook.bids) + len(orderbook.asks),
            'thin_ratio': (thin_bids + thin_asks) / max(1, len(orderbook.bids) + len(orderbook.asks)),
            'potential_manipulation': thin_bids > 5 or thin_asks > 5
        }

    # ==========================================
    # API AUTHENTICATION
    # ==========================================

    def generate_timestamp(self) -> int:
        """Generate timestamp for API requests"""
        return int(time.time())

    def generate_nonce(self) -> str:
        """Generate unique nonce for orders"""
        return str(int(time.time() * 1000000))

    def create_hmac_signature(self, secret: str, timestamp: int,
                              method: str, path: str,
                              body: str = "") -> str:
        """Create HMAC signature for authenticated requests"""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def build_auth_headers(self, api_key: str, api_secret: str,
                           api_passphrase: str, timestamp: int,
                           method: str, path: str, body: str = "") -> Dict:
        """Build authentication headers for CLOB API"""
        signature = self.create_hmac_signature(api_secret, timestamp, method, path, body)

        return {
            'POLY-ADDRESS': '',  # Set by caller
            'POLY-SIGNATURE': signature,
            'POLY-TIMESTAMP': str(timestamp),
            'POLY-API-KEY': api_key,
            'POLY-PASSPHRASE': api_passphrase
        }

    # ==========================================
    # EIP-712 ORDER SIGNING
    # ==========================================

    EIP712_DOMAIN = {
        'name': 'Polymarket CTF Exchange',
        'version': '1',
        'chainId': 137
    }

    ORDER_TYPES = {
        'Order': [
            {'name': 'salt', 'type': 'uint256'},
            {'name': 'maker', 'type': 'address'},
            {'name': 'signer', 'type': 'address'},
            {'name': 'taker', 'type': 'address'},
            {'name': 'tokenId', 'type': 'uint256'},
            {'name': 'makerAmount', 'type': 'uint256'},
            {'name': 'takerAmount', 'type': 'uint256'},
            {'name': 'expiration', 'type': 'uint256'},
            {'name': 'nonce', 'type': 'uint256'},
            {'name': 'feeRateBps', 'type': 'uint256'},
            {'name': 'side', 'type': 'uint8'},
            {'name': 'signatureType', 'type': 'uint8'}
        ]
    }

    def build_eip712_order(self, maker: str, token_id: str, side: str,
                           price: float, size: float,
                           expiration: int = 0, nonce: str = None) -> Dict:
        """Build EIP-712 typed data for order signing"""
        if nonce is None:
            nonce = self.generate_nonce()

        # Convert to contract format
        # For BUY: maker provides USDC (takerAmount), receives tokens (makerAmount)
        # For SELL: maker provides tokens (makerAmount), receives USDC (takerAmount)
        usdc_amount = int(size * price * 1e6)  # USDC has 6 decimals
        token_amount = int(size * 1e6)          # Tokens have 6 decimals

        if side.upper() == 'BUY':
            maker_amount = token_amount
            taker_amount = usdc_amount
            side_int = 0
        else:
            maker_amount = usdc_amount
            taker_amount = token_amount
            side_int = 1

        order_data = {
            'salt': int(nonce),
            'maker': maker,
            'signer': maker,
            'taker': '0x0000000000000000000000000000000000000000',
            'tokenId': int(token_id) if token_id.isdigit() else 0,
            'makerAmount': maker_amount,
            'takerAmount': taker_amount,
            'expiration': expiration,
            'nonce': 0,
            'feeRateBps': 0,
            'side': side_int,
            'signatureType': 2  # EIP712
        }

        return {
            'types': self.ORDER_TYPES,
            'domain': self.EIP712_DOMAIN,
            'primaryType': 'Order',
            'message': order_data
        }

    # ==========================================
    # MARKET DATA PARSING
    # ==========================================

    def parse_market(self, data: Dict) -> Dict:
        """Parse market data from API response"""
        return {
            'condition_id': data.get('condition_id', ''),
            'question_id': data.get('question_id', ''),
            'question': data.get('question', ''),
            'description': data.get('description', ''),
            'market_slug': data.get('market_slug', ''),
            'end_date_iso': data.get('end_date_iso', ''),
            'active': data.get('active', False),
            'closed': data.get('closed', False),
            'archived': data.get('archived', False),
            'tokens': data.get('tokens', []),
            'minimum_order_size': data.get('minimum_order_size', self.MIN_ORDER_SIZE),
            'minimum_tick_size': data.get('minimum_tick_size', self.MIN_TICK_SIZE)
        }

    def parse_trade(self, data: Dict) -> Trade:
        """Parse trade data from API response"""
        return Trade(
            trade_id=data.get('id', ''),
            token_id=data.get('asset_id', ''),
            side=Side(data.get('side', 'BUY')),
            price=float(data.get('price', 0)),
            size=float(data.get('size', 0)),
            timestamp=datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
            if data.get('timestamp') else datetime.now(),
            maker_order_id=data.get('maker_order_id', ''),
            taker_order_id=data.get('taker_order_id', ''),
            maker_address=data.get('maker_address', ''),
            taker_address=data.get('taker_address', ''),
            fee=float(data.get('fee', 0))
        )

    def parse_order(self, data: Dict) -> Order:
        """Parse order data from API response"""
        return Order(
            order_id=data.get('id', ''),
            token_id=data.get('asset_id', ''),
            side=Side(data.get('side', 'BUY')),
            price=float(data.get('price', 0)),
            size=float(data.get('original_size', data.get('size', 0))),
            order_type=OrderType(data.get('type', 'GTC')),
            status=OrderStatus(data.get('status', 'LIVE')),
            created_at=datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
            if data.get('created_at') else datetime.now(),
            filled_size=float(data.get('size_matched', 0)),
            maker_address=data.get('maker_address', ''),
            signature=data.get('signature', '')
        )

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================

    def format_price(self, price: float) -> str:
        """Format price for display"""
        return f"${price:.3f}"

    def format_size(self, size: float) -> str:
        """Format size for display"""
        if size >= 1000:
            return f"{size/1000:.1f}K"
        return f"{size:.2f}"

    def tokens_to_usdc(self, tokens: float, price: float) -> float:
        """Convert token amount to USDC value"""
        return tokens * price

    def usdc_to_tokens(self, usdc: float, price: float) -> float:
        """Convert USDC to token amount"""
        if price <= 0:
            return 0
        return usdc / price

    def calculate_returns(self, entry_price: float, exit_price: float,
                          side: str) -> Dict:
        """Calculate returns from trade"""
        if side.upper() == 'BUY':
            pnl = exit_price - entry_price
            pnl_percent = (exit_price / entry_price - 1) * 100 if entry_price > 0 else 0
        else:
            pnl = entry_price - exit_price
            pnl_percent = (entry_price / exit_price - 1) * 100 if exit_price > 0 else 0

        return {
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'direction': 'profit' if pnl > 0 else 'loss' if pnl < 0 else 'breakeven'
        }


# Singleton instance
clob = PolymarketCLOB()
