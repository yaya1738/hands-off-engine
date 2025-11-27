# Polymarket CLOB API Client

This document describes the Polymarket CLOB (Central Limit Order Book) API client
for the Hands-Off Engine, used for executing real trades on Polymarket.

## Overview

The `PolymarketClient` class provides a safe, audited interface to the Polymarket
trading API. It supports:

- Order placement (BUY/SELL)
- Balance queries
- Position management
- Order cancellation
- Rate limiting and retry logic
- Comprehensive error handling
- Audit trail logging

**IMPORTANT:** DRYRUN mode is enabled by default. No real trades will be executed
unless explicitly configured.

## Prerequisites

### Environment Variables

Set these environment variables or pass credentials directly to the client:

```bash
export POLYMARKET_API_KEY="your_api_key"
export POLYMARKET_API_SECRET="your_api_secret"
export POLYMARKET_API_PASSPHRASE="your_passphrase"
export POLYMARKET_WALLET_ADDRESS="0xYourPolygonWalletAddress"
```

### Getting API Credentials

1. Visit [Polymarket](https://polymarket.com) and connect your wallet
2. Go to the API section in your account settings
3. Create or derive API credentials (key, secret, passphrase)
4. Store credentials securely (never commit to git!)

For detailed instructions, see:
- [Polymarket Authentication Docs](https://docs.polymarket.com/developers/CLOB/authentication)

## Quick Start

### Basic Usage (DRYRUN Mode)

```python
from scripts.polymarket_client import PolymarketClient, OrderSide

# Create client (DRYRUN by default)
client = PolymarketClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    api_passphrase="your_passphrase",
    wallet_address="0x1234567890abcdef1234567890abcdef12345678"
)

# Get balance
balance = client.get_balance()
print(f"USDC Balance: ${balance.usdc_balance:.2f}")

# Place order (simulated in DRYRUN)
result = client.place_order(
    market_id="0xMarketConditionId",
    side=OrderSide.BUY,
    size_usd=50.0,
    price=0.55
)
print(f"Order: {result.message}")

# Get positions
positions = client.get_positions()
for pos in positions:
    print(f"Position: {pos.market_id} - {pos.side} - {pos.size}")

# Cancel order
client.cancel_order(result.order_id)

client.close()
```

### Using Environment Variables

```python
# Credentials from environment variables
client = PolymarketClient()  # Uses POLYMARKET_* env vars
```

### Context Manager

```python
with PolymarketClient() as client:
    balance = client.get_balance()
    # Session automatically closed on exit
```

## API Reference

### PolymarketClient

```python
PolymarketClient(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    api_passphrase: Optional[str] = None,
    wallet_address: Optional[str] = None,
    dryrun: bool = True,
    base_url: Optional[str] = None
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| api_key | str | None | API key (or `POLYMARKET_API_KEY` env var) |
| api_secret | str | None | API secret (or `POLYMARKET_API_SECRET` env var) |
| api_passphrase | str | None | API passphrase (or `POLYMARKET_API_PASSPHRASE` env var) |
| wallet_address | str | None | Polygon wallet address (or `POLYMARKET_WALLET_ADDRESS` env var) |
| dryrun | bool | True | **SAFETY**: If True, no real trades are executed |
| base_url | str | None | Override API base URL (for testing) |

### Methods

#### `get_balance() -> Balance`

Get account USDC balance.

```python
balance = client.get_balance()
print(f"Available: ${balance.available_balance:.2f}")
```

Returns:
- `Balance` object with `usdc_balance` and `available_balance`

#### `get_positions() -> List[Position]`

Get current market positions.

```python
positions = client.get_positions()
for pos in positions:
    print(f"{pos.market_id}: {pos.size} @ {pos.avg_price}")
```

Returns:
- List of `Position` objects

#### `place_order(...) -> OrderResult`

Place a limit order.

```python
result = client.place_order(
    market_id="0xMarketId",
    side=OrderSide.BUY,  # or OrderSide.SELL
    size_usd=50.0,       # Order size in USD
    price=0.55,          # Limit price (0.0 to 1.0)
    order_type=OrderType.GTC,  # Optional: GTC, GTD, FOK
    token_id=None        # Optional: specific token ID
)
```

Parameters:
- `market_id`: Market condition ID
- `side`: `OrderSide.BUY` or `OrderSide.SELL`
- `size_usd`: Order size in USD
- `price`: Limit price between 0.0 and 1.0
- `order_type`: Order type (default: GTC)
- `token_id`: Optional specific token ID

Returns:
- `OrderResult` with success status, order ID, and details

#### `cancel_order(order_id: str) -> bool`

Cancel a specific order.

```python
success = client.cancel_order("order_id_123")
```

#### `cancel_all_orders() -> int`

Cancel all open orders.

```python
count = client.cancel_all_orders()
print(f"Cancelled {count} orders")
```

#### `get_open_orders() -> List[Dict]`

Get list of open orders.

```python
orders = client.get_open_orders()
for order in orders:
    print(order)
```

#### `get_market(market_id: str) -> Dict`

Get market details.

```python
market = client.get_market("0xMarketId")
print(market["question"])
```

## Error Handling

The client raises specific exceptions for different error conditions:

```python
from scripts.polymarket_client import (
    PolymarketError,        # Base exception
    AuthenticationError,    # Invalid credentials
    InsufficientFundsError, # Not enough balance
    InvalidMarketError,     # Market not found
    RateLimitError,         # Rate limit exceeded
    OrderError              # Order placement/cancellation failed
)

try:
    result = client.place_order(...)
except InsufficientFundsError:
    print("Not enough funds!")
except InvalidMarketError:
    print("Market not found!")
except OrderError as e:
    print(f"Order failed: {e}")
```

## Rate Limiting

The client automatically:
- Limits requests to 10/second
- Delays between requests (100ms default)
- Retries on transient failures (3 attempts)
- Handles 429 responses with exponential backoff

## Audit Logging

All API calls are logged to the audit trail:
- Order placements
- Balance/position queries
- Cancellations
- Errors

Logs are written to `logs/audit/audit_YYYY-MM-DD.jsonl`.

## Safety Features

### DRYRUN Mode (Default)

By default, the client operates in DRYRUN mode:
- No real trades are executed
- Orders return simulated success
- Balance returns mock values

To enable LIVE trading:

```python
# ⚠️ WARNING: This executes REAL trades!
client = PolymarketClient(dryrun=False)
```

### Validation

The client validates:
- Price must be between 0 and 1
- Size must be positive
- Market ID must be provided
- Credentials must be set for LIVE mode

## Finding Market IDs

Market IDs (condition IDs) can be found:

1. Via the Gamma API:
   ```bash
   curl https://gamma-api.polymarket.com/events
   ```

2. Via the client:
   ```python
   market = client.get_market("0xMarketId")
   ```

3. From the Polymarket website URL

## Integration with Executor

The client integrates with the Hands-Off Engine executor:

```python
from executor.ho_executor_plan import Executor
from scripts.polymarket_client import PolymarketClient, OrderSide

# In production, the executor would use the client:
client = PolymarketClient(dryrun=True)

# Executor validates actions before passing to client
executor = Executor(dryrun=True)
```

## Testing

Run the unit tests:

```bash
python -m pytest tests/unit/test_polymarket_client.py -v
```

## References

- [Polymarket CLOB Documentation](https://docs.polymarket.com/developers/CLOB/)
- [Authentication Guide](https://docs.polymarket.com/developers/CLOB/authentication)
- [Order Endpoints](https://docs.polymarket.com/developers/CLOB/orders/create-order)
- [Cancel Orders](https://docs.polymarket.com/developers/CLOB/orders/cancel-orders)

## Security Notes

- Never commit API credentials to version control
- Use environment variables for credentials
- Keep DRYRUN enabled during development
- Monitor audit logs for unusual activity
- Set appropriate position size limits
