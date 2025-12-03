"""
Polymarket Order Management
===========================

Complete order management functionality including:
- All order types (GTC, GTD, FOK, IOC)
- Order lifecycle management
- Order matching and execution
- Batch operations
- Order amendment
- Cancel strategies

ORDER TYPES:
-----------
GTC (Good Till Cancelled):
    - Default order type
    - Remains active until filled or cancelled
    - Best for passive market making

GTD (Good Till Date):
    - Expires at specified timestamp
    - Useful for time-sensitive strategies
    - Auto-cancels at expiration

FOK (Fill Or Kill):
    - Must fill entirely or cancel
    - No partial fills
    - Best for large orders needing atomicity

IOC (Immediate Or Cancel):
    - Fill what's available, cancel rest
    - Good for taking liquidity
    - Accepts partial fills

USAGE:
    from executor.polymarket.orders import orders

    orders.create_limit_order('BUY', token_id, 0.65, 100)
    orders.calculate_required_balance(0.65, 100, 'BUY')
    orders.batch_orders([order1, order2, order3])
"""

import time
import uuid
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    GTC = "GTC"   # Good Till Cancelled
    GTD = "GTD"   # Good Till Date
    FOK = "FOK"   # Fill Or Kill
    IOC = "IOC"   # Immediate Or Cancel


class OrderStatus(Enum):
    PENDING = "PENDING"       # Not yet submitted
    LIVE = "LIVE"             # Active on book
    PARTIAL = "PARTIAL"       # Partially filled
    MATCHED = "MATCHED"       # Fully filled
    CANCELLED = "CANCELLED"   # User cancelled
    EXPIRED = "EXPIRED"       # GTD expired
    REJECTED = "REJECTED"     # Failed validation


class CancelReason(Enum):
    USER_REQUEST = "user_request"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    MARKET_CLOSED = "market_closed"
    EXPIRED = "expired"
    SELF_TRADE = "self_trade"
    POST_ONLY_WOULD_TAKE = "post_only_would_take"


@dataclass
class OrderParams:
    """Parameters for creating an order"""
    side: OrderSide
    token_id: str
    price: float
    size: float
    order_type: OrderType = OrderType.GTC
    expiration: Optional[datetime] = None
    post_only: bool = False  # Only maker, fail if would take
    reduce_only: bool = False  # Only reduce position
    client_order_id: str = ""

    def __post_init__(self):
        if not self.client_order_id:
            self.client_order_id = str(uuid.uuid4())[:8]


@dataclass
class OrderState:
    """Complete order state tracking"""
    order_id: str
    params: OrderParams
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    filled_size: float = 0.0
    average_fill_price: float = 0.0
    fills: List[Dict] = field(default_factory=list)
    cancel_reason: Optional[CancelReason] = None

    @property
    def remaining_size(self) -> float:
        return self.params.size - self.filled_size

    @property
    def is_active(self) -> bool:
        return self.status in [OrderStatus.LIVE, OrderStatus.PARTIAL]

    @property
    def is_done(self) -> bool:
        return self.status in [OrderStatus.MATCHED, OrderStatus.CANCELLED,
                               OrderStatus.EXPIRED, OrderStatus.REJECTED]

    @property
    def fill_percent(self) -> float:
        return (self.filled_size / self.params.size * 100) if self.params.size > 0 else 0


class OrderManager:
    """
    Order management for Polymarket trading.

    Handles order creation, validation, lifecycle, and batch operations.
    """

    # Constraints
    MIN_PRICE = 0.001
    MAX_PRICE = 0.999
    MIN_SIZE = 0.01
    MAX_SIZE = 100000
    TICK_SIZE = 0.001
    MAX_ORDERS_PER_MARKET = 100
    MAX_BATCH_SIZE = 50

    # ==========================================
    # ORDER CREATION
    # ==========================================

    def create_limit_order(self, side: str, token_id: str, price: float,
                           size: float, order_type: str = "GTC",
                           expiration: Optional[datetime] = None,
                           post_only: bool = False) -> OrderParams:
        """Create a limit order with validation"""
        # Normalize inputs
        side_enum = OrderSide(side.upper())
        order_type_enum = OrderType(order_type.upper())
        price = self.normalize_price(price)
        size = self.normalize_size(size)

        # Validate
        validation = self.validate_order_params(price, size, order_type_enum)
        if not validation['valid']:
            raise ValueError(f"Invalid order: {validation['errors']}")

        return OrderParams(
            side=side_enum,
            token_id=token_id,
            price=price,
            size=size,
            order_type=order_type_enum,
            expiration=expiration,
            post_only=post_only
        )

    def create_market_order(self, side: str, token_id: str,
                            size: float) -> OrderParams:
        """
        Create a market order (IOC at aggressive price).

        Market orders on Polymarket are IOC limit orders at
        aggressive prices (0.999 for buy, 0.001 for sell).
        """
        price = self.MAX_PRICE if side.upper() == "BUY" else self.MIN_PRICE
        return self.create_limit_order(side, token_id, price, size, "IOC")

    def create_gtd_order(self, side: str, token_id: str, price: float,
                         size: float, expires_in: timedelta) -> OrderParams:
        """Create order that expires after specified duration"""
        expiration = datetime.now() + expires_in
        return self.create_limit_order(side, token_id, price, size, "GTD", expiration)

    def create_fok_order(self, side: str, token_id: str, price: float,
                         size: float) -> OrderParams:
        """Create fill-or-kill order"""
        return self.create_limit_order(side, token_id, price, size, "FOK")

    # ==========================================
    # ORDER VALIDATION
    # ==========================================

    def normalize_price(self, price: float) -> float:
        """Round price to valid tick size"""
        normalized = round(price / self.TICK_SIZE) * self.TICK_SIZE
        return max(self.MIN_PRICE, min(self.MAX_PRICE, normalized))

    def normalize_size(self, size: float) -> float:
        """Round size to valid precision"""
        return round(max(0, size), 2)

    def validate_order_params(self, price: float, size: float,
                              order_type: OrderType) -> Dict:
        """Comprehensive order validation"""
        errors = []
        warnings = []

        # Price validation
        if price < self.MIN_PRICE:
            errors.append(f"Price {price} below minimum {self.MIN_PRICE}")
        if price > self.MAX_PRICE:
            errors.append(f"Price {price} above maximum {self.MAX_PRICE}")

        # Size validation
        if size < self.MIN_SIZE:
            errors.append(f"Size {size} below minimum {self.MIN_SIZE}")
        if size > self.MAX_SIZE:
            errors.append(f"Size {size} above maximum {self.MAX_SIZE}")

        # Type-specific validation
        if order_type == OrderType.GTD:
            warnings.append("GTD orders require valid expiration timestamp")

        if order_type == OrderType.FOK and size > 1000:
            warnings.append("Large FOK orders may fail to fill")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_balance(self, side: OrderSide, price: float, size: float,
                         usdc_balance: float, token_balance: float) -> Dict:
        """Validate sufficient balance for order"""
        required = self.calculate_required_balance(price, size, side.value)

        if side == OrderSide.BUY:
            has_balance = usdc_balance >= required['usdc']
        else:
            has_balance = token_balance >= required['tokens']

        return {
            'valid': has_balance,
            'required_usdc': required['usdc'],
            'required_tokens': required['tokens'],
            'available_usdc': usdc_balance,
            'available_tokens': token_balance
        }

    # ==========================================
    # BALANCE CALCULATIONS
    # ==========================================

    def calculate_required_balance(self, price: float, size: float,
                                   side: str) -> Dict:
        """Calculate required balance for order"""
        if side.upper() == "BUY":
            # Need USDC to buy
            usdc_required = size * price
            tokens_required = 0.0
        else:
            # Need tokens to sell
            usdc_required = 0.0
            tokens_required = size

        return {
            'usdc': usdc_required,
            'tokens': tokens_required,
            'total_value': size * price
        }

    def max_order_size(self, balance: float, price: float, side: str) -> float:
        """Calculate maximum order size given balance"""
        if side.upper() == "BUY":
            if price <= 0:
                return 0
            return balance / price
        else:
            return balance  # Token balance = max sell size

    def cost_basis(self, fills: List[Dict]) -> Dict:
        """Calculate cost basis from fills"""
        total_size = sum(f['size'] for f in fills)
        total_cost = sum(f['size'] * f['price'] for f in fills)

        if total_size == 0:
            return {'average_price': 0, 'total_size': 0, 'total_cost': 0}

        return {
            'average_price': total_cost / total_size,
            'total_size': total_size,
            'total_cost': total_cost
        }

    # ==========================================
    # ORDER MATCHING LOGIC
    # ==========================================

    def would_match(self, order_price: float, side: OrderSide,
                    best_bid: float, best_ask: float) -> bool:
        """Check if order would immediately match"""
        if side == OrderSide.BUY:
            return order_price >= best_ask
        else:
            return order_price <= best_bid

    def crossing_spread(self, bid_price: float, ask_price: float,
                        order_price: float, side: OrderSide) -> bool:
        """Check if order crosses the spread"""
        if side == OrderSide.BUY:
            return order_price >= ask_price
        else:
            return order_price <= bid_price

    def post_only_would_fail(self, order_price: float, side: OrderSide,
                             best_bid: float, best_ask: float) -> bool:
        """Check if post-only order would be rejected"""
        return self.would_match(order_price, side, best_bid, best_ask)

    def self_trade_check(self, order: OrderParams,
                         existing_orders: List[OrderParams]) -> bool:
        """Check if order would self-trade with existing orders"""
        for existing in existing_orders:
            if existing.token_id != order.token_id:
                continue
            if existing.side == order.side:
                continue

            # Check for price overlap
            if order.side == OrderSide.BUY:
                if order.price >= existing.price:
                    return True  # Buy crosses existing sell
            else:
                if order.price <= existing.price:
                    return True  # Sell crosses existing buy

        return False

    # ==========================================
    # BATCH OPERATIONS
    # ==========================================

    def batch_orders(self, orders: List[OrderParams]) -> Dict:
        """Prepare batch of orders for submission"""
        if len(orders) > self.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(orders)} exceeds max {self.MAX_BATCH_SIZE}")

        validated = []
        errors = []

        for i, order in enumerate(orders):
            validation = self.validate_order_params(
                order.price, order.size, order.order_type
            )
            if validation['valid']:
                validated.append(order)
            else:
                errors.append({'index': i, 'errors': validation['errors']})

        return {
            'valid_orders': validated,
            'errors': errors,
            'total': len(orders),
            'valid_count': len(validated),
            'error_count': len(errors)
        }

    def batch_cancel_params(self, order_ids: List[str] = None,
                            token_id: str = None) -> Dict:
        """Build parameters for batch cancel"""
        if order_ids:
            return {
                'type': 'by_ids',
                'order_ids': order_ids
            }
        elif token_id:
            return {
                'type': 'by_market',
                'token_id': token_id
            }
        else:
            return {
                'type': 'cancel_all'
            }

    # ==========================================
    # ORDER AMENDMENT
    # ==========================================

    def can_amend(self, order: OrderState) -> bool:
        """Check if order can be amended"""
        return order.status in [OrderStatus.LIVE, OrderStatus.PARTIAL]

    def amend_price(self, order: OrderParams, new_price: float) -> OrderParams:
        """Amend order price (creates new order params)"""
        return OrderParams(
            side=order.side,
            token_id=order.token_id,
            price=self.normalize_price(new_price),
            size=order.size,
            order_type=order.order_type,
            expiration=order.expiration,
            post_only=order.post_only
        )

    def amend_size(self, order: OrderParams, new_size: float,
                   filled_size: float = 0) -> OrderParams:
        """Amend order size (creates new order params)"""
        # Can only increase remaining or reduce if partially filled
        new_remaining = new_size - filled_size
        if new_remaining <= 0:
            raise ValueError("New size must be greater than filled amount")

        return OrderParams(
            side=order.side,
            token_id=order.token_id,
            price=order.price,
            size=self.normalize_size(new_size),
            order_type=order.order_type,
            expiration=order.expiration,
            post_only=order.post_only
        )

    # ==========================================
    # ORDER BOOK PLACEMENT
    # ==========================================

    def queue_position_estimate(self, order_price: float, side: OrderSide,
                                orderbook_levels: List[Dict]) -> Dict:
        """Estimate queue position for limit order"""
        same_price_size = 0
        better_price_size = 0

        for level in orderbook_levels:
            level_price = level['price']
            level_size = level['size']

            if side == OrderSide.BUY:
                if level_price > order_price:
                    better_price_size += level_size
                elif level_price == order_price:
                    same_price_size += level_size
            else:
                if level_price < order_price:
                    better_price_size += level_size
                elif level_price == order_price:
                    same_price_size += level_size

        return {
            'ahead_in_queue': better_price_size,
            'at_same_price': same_price_size,
            'estimated_fill_time': 'indeterminate',  # Would need historical data
            'position': 'back_of_queue' if same_price_size > 0 else 'new_level'
        }

    def price_improvement(self, order_price: float, side: OrderSide,
                          best_bid: float, best_ask: float) -> Dict:
        """Calculate price improvement from order"""
        mid = (best_bid + best_ask) / 2

        if side == OrderSide.BUY:
            # Buy improving if price < mid
            improvement = mid - order_price
            is_improving = order_price < mid
        else:
            # Sell improving if price > mid
            improvement = order_price - mid
            is_improving = order_price > mid

        return {
            'mid_price': mid,
            'order_price': order_price,
            'improvement': improvement,
            'improvement_bps': (improvement / mid * 10000) if mid > 0 else 0,
            'is_improving': is_improving
        }

    # ==========================================
    # SMART ORDER TYPES
    # ==========================================

    def bracket_orders(self, entry_side: str, token_id: str,
                       entry_price: float, size: float,
                       take_profit: float, stop_loss: float) -> List[OrderParams]:
        """
        Create bracket order set (entry + TP + SL).

        Note: Polymarket doesn't have native bracket orders,
        these would need to be managed externally.
        """
        orders = []

        # Entry order
        entry = self.create_limit_order(entry_side, token_id, entry_price, size)
        orders.append(entry)

        # Exit orders (opposite side)
        exit_side = "SELL" if entry_side.upper() == "BUY" else "BUY"

        # Take profit
        tp = self.create_limit_order(exit_side, token_id, take_profit, size)
        orders.append(tp)

        # Stop loss (would need external monitoring)
        sl = self.create_limit_order(exit_side, token_id, stop_loss, size)
        orders.append(sl)

        return orders

    def scale_in_orders(self, side: str, token_id: str, prices: List[float],
                        total_size: float, distribution: str = "equal") -> List[OrderParams]:
        """
        Create scaled entry orders at multiple prices.

        Distributions:
        - equal: Same size at each level
        - pyramid: More at better prices
        - reverse_pyramid: More at worse prices
        """
        n = len(prices)
        orders = []

        if distribution == "equal":
            sizes = [total_size / n] * n
        elif distribution == "pyramid":
            # More weight at better prices (front of list)
            weights = list(range(n, 0, -1))
            total_weight = sum(weights)
            sizes = [total_size * w / total_weight for w in weights]
        elif distribution == "reverse_pyramid":
            # More weight at worse prices
            weights = list(range(1, n + 1))
            total_weight = sum(weights)
            sizes = [total_size * w / total_weight for w in weights]
        else:
            sizes = [total_size / n] * n

        for price, size in zip(prices, sizes):
            order = self.create_limit_order(side, token_id, price, size)
            orders.append(order)

        return orders

    def iceberg_orders(self, side: str, token_id: str, price: float,
                       total_size: float, visible_size: float) -> List[OrderParams]:
        """
        Create iceberg order (hidden liquidity).

        Note: Polymarket doesn't have native iceberg support,
        this creates multiple orders that would be submitted sequentially.
        """
        orders = []
        remaining = total_size

        while remaining > 0:
            size = min(visible_size, remaining)
            order = self.create_limit_order(side, token_id, price, size)
            orders.append(order)
            remaining -= size

        return orders

    # ==========================================
    # ORDER TRACKING
    # ==========================================

    def order_summary(self, orders: List[OrderState]) -> Dict:
        """Summarize multiple orders"""
        by_status = {}
        by_side = {'BUY': [], 'SELL': []}
        total_value = 0
        total_filled = 0

        for order in orders:
            status = order.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(order)

            by_side[order.params.side.value].append(order)
            total_value += order.params.price * order.params.size
            total_filled += order.filled_size

        return {
            'total_orders': len(orders),
            'by_status': {k: len(v) for k, v in by_status.items()},
            'by_side': {k: len(v) for k, v in by_side.items()},
            'total_value': total_value,
            'total_filled': total_filled,
            'active_orders': len(by_status.get('LIVE', [])) + len(by_status.get('PARTIAL', []))
        }

    def fill_rate(self, orders: List[OrderState],
                  time_window: timedelta = None) -> Dict:
        """Calculate fill rate statistics"""
        if not orders:
            return {'fill_rate': 0, 'avg_fill_time': 0}

        total_size = sum(o.params.size for o in orders)
        filled_size = sum(o.filled_size for o in orders)
        fully_filled = sum(1 for o in orders if o.status == OrderStatus.MATCHED)

        return {
            'fill_rate_by_size': filled_size / total_size * 100 if total_size > 0 else 0,
            'fill_rate_by_count': fully_filled / len(orders) * 100,
            'total_orders': len(orders),
            'fully_filled': fully_filled,
            'total_size': total_size,
            'filled_size': filled_size
        }


# Singleton instance
orders = OrderManager()
