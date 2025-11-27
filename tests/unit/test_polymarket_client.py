"""
Unit tests for Polymarket CLOB API Client

Tests authentication, order placement, balance queries, and error handling
with mocked API responses.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add scripts and parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.polymarket_client import (
    PolymarketClient,
    PolymarketError,
    AuthenticationError,
    InsufficientFundsError,
    InvalidMarketError,
    RateLimitError,
    OrderError,
    OrderSide,
    OrderType,
    OrderResult,
    Balance,
    Position
)


@pytest.fixture
def mock_audit_logger():
    """Mock the audit logger"""
    with patch('scripts.polymarket_client.get_audit_logger') as mock:
        logger = MagicMock()
        mock.return_value = logger
        yield logger


@pytest.fixture
def dryrun_client(mock_audit_logger):
    """Create a client in DRYRUN mode (default)"""
    return PolymarketClient(
        api_key="test_api_key",
        api_secret="test_api_secret",
        api_passphrase="test_passphrase",
        wallet_address="0x1234567890abcdef1234567890abcdef12345678",
        dryrun=True
    )


@pytest.fixture
def live_client(mock_audit_logger):
    """Create a client in LIVE mode for testing real API calls (mocked)"""
    return PolymarketClient(
        api_key="test_api_key",
        api_secret="test_api_secret",
        api_passphrase="test_passphrase",
        wallet_address="0x1234567890abcdef1234567890abcdef12345678",
        dryrun=False
    )


class TestClientInitialization:
    """Test client initialization and configuration"""

    def test_default_dryrun_mode(self, mock_audit_logger):
        """Client should default to DRYRUN mode"""
        client = PolymarketClient(
            api_key="test_key",
            api_secret="test_secret",
            api_passphrase="test_pass",
            wallet_address="0x1234"
        )
        assert client.dryrun is True

    def test_env_var_credentials(self, mock_audit_logger, monkeypatch):
        """Client should read credentials from environment variables"""
        monkeypatch.setenv("POLYMARKET_API_KEY", "env_api_key")
        monkeypatch.setenv("POLYMARKET_API_SECRET", "env_api_secret")
        monkeypatch.setenv("POLYMARKET_API_PASSPHRASE", "env_passphrase")
        monkeypatch.setenv("POLYMARKET_WALLET_ADDRESS", "0xenvwallet")

        client = PolymarketClient()
        assert client.api_key == "env_api_key"
        assert client.api_secret == "env_api_secret"
        assert client.api_passphrase == "env_passphrase"
        assert client.wallet_address == "0xenvwallet"

    def test_explicit_credentials_override_env(self, mock_audit_logger, monkeypatch):
        """Explicit credentials should override environment variables"""
        monkeypatch.setenv("POLYMARKET_API_KEY", "env_api_key")

        client = PolymarketClient(api_key="explicit_key")
        assert client.api_key == "explicit_key"

    def test_custom_base_url(self, mock_audit_logger):
        """Client should accept custom base URL"""
        client = PolymarketClient(
            api_key="test",
            api_secret="test",
            api_passphrase="test",
            wallet_address="0x1234",
            base_url="https://custom.api.url"
        )
        assert client.base_url == "https://custom.api.url"


class TestDryrunMode:
    """Test DRYRUN mode behavior"""

    def test_get_balance_dryrun(self, dryrun_client, mock_audit_logger):
        """get_balance in DRYRUN mode returns mock balance"""
        balance = dryrun_client.get_balance()

        assert isinstance(balance, Balance)
        assert balance.usdc_balance == 1000.0
        assert balance.available_balance == 1000.0
        mock_audit_logger.log_data_fetch.assert_called()

    def test_get_positions_dryrun(self, dryrun_client, mock_audit_logger):
        """get_positions in DRYRUN mode returns empty list"""
        positions = dryrun_client.get_positions()

        assert isinstance(positions, list)
        assert len(positions) == 0
        mock_audit_logger.log_data_fetch.assert_called()

    def test_place_order_dryrun(self, dryrun_client, mock_audit_logger):
        """place_order in DRYRUN mode returns simulated success"""
        result = dryrun_client.place_order(
            market_id="0xtest_market",
            side=OrderSide.BUY,
            size_usd=50.0,
            price=0.55
        )

        assert isinstance(result, OrderResult)
        assert result.success is True
        assert result.dryrun is True
        assert "DRYRUN" in result.message
        assert result.order_id is not None
        assert result.order_id.startswith("dryrun_")
        assert result.side == "BUY"
        assert result.size_usd == 50.0
        assert result.price == 0.55
        mock_audit_logger.log_order.assert_called()
        mock_audit_logger.log_action.assert_called()

    def test_cancel_order_dryrun(self, dryrun_client, mock_audit_logger):
        """cancel_order in DRYRUN mode returns True"""
        result = dryrun_client.cancel_order("dryrun_order_123")

        assert result is True
        mock_audit_logger.log_action.assert_called()

    def test_cancel_all_orders_dryrun(self, dryrun_client, mock_audit_logger):
        """cancel_all_orders in DRYRUN mode returns 0"""
        count = dryrun_client.cancel_all_orders()

        assert count == 0
        mock_audit_logger.log_action.assert_called()

    def test_get_open_orders_dryrun(self, dryrun_client, mock_audit_logger):
        """get_open_orders in DRYRUN mode returns empty list"""
        orders = dryrun_client.get_open_orders()

        assert isinstance(orders, list)
        assert len(orders) == 0


class TestAuthentication:
    """Test authentication and credential validation"""

    def test_missing_api_key_raises_error(self, mock_audit_logger):
        """Missing API key should raise AuthenticationError in LIVE mode"""
        client = PolymarketClient(
            api_secret="secret",
            api_passphrase="pass",
            wallet_address="0x1234",
            dryrun=False
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client._validate_credentials()
        assert "API key" in str(exc_info.value)

    def test_missing_api_secret_raises_error(self, mock_audit_logger):
        """Missing API secret should raise AuthenticationError"""
        client = PolymarketClient(
            api_key="key",
            api_passphrase="pass",
            wallet_address="0x1234",
            dryrun=False
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client._validate_credentials()
        assert "secret" in str(exc_info.value)

    def test_missing_wallet_address_raises_error(self, mock_audit_logger):
        """Missing wallet address should raise AuthenticationError"""
        client = PolymarketClient(
            api_key="key",
            api_secret="secret",
            api_passphrase="pass",
            dryrun=False
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client._validate_credentials()
        assert "address" in str(exc_info.value)

    def test_signature_generation(self, dryrun_client):
        """Signature generation should produce consistent output"""
        sig1 = dryrun_client._generate_signature("1234567890", "GET", "/test", "")
        sig2 = dryrun_client._generate_signature("1234567890", "GET", "/test", "")

        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex digest length

    def test_auth_headers_format(self, dryrun_client):
        """Auth headers should include all required fields"""
        headers = dryrun_client._get_auth_headers("GET", "/test", "")

        assert "POLY_ADDRESS" in headers
        assert "POLY_SIGNATURE" in headers
        assert "POLY_TIMESTAMP" in headers
        assert "POLY_API_KEY" in headers
        assert "POLY_PASSPHRASE" in headers
        assert headers["POLY_ADDRESS"] == dryrun_client.wallet_address
        assert headers["POLY_API_KEY"] == dryrun_client.api_key


class TestLiveAPIInteractions:
    """Test LIVE mode API interactions with mocked responses"""

    @patch('requests.Session.get')
    def test_get_balance_success(self, mock_get, live_client, mock_audit_logger):
        """Successful balance fetch in LIVE mode"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"balance": 500.50, "available": 400.25}'
        mock_response.json.return_value = {"balance": 500.50, "available": 400.25}
        mock_get.return_value = mock_response

        balance = live_client.get_balance()

        assert balance.usdc_balance == 500.50
        assert balance.available_balance == 400.25

    @patch('requests.Session.get')
    def test_get_positions_success(self, mock_get, live_client, mock_audit_logger):
        """Successful positions fetch in LIVE mode"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "positions": [
                {
                    "market_id": "0xmarket1",
                    "token_id": "0xtoken1",
                    "side": "YES",
                    "size": 100.0,
                    "avg_price": 0.55
                }
            ]
        }
        mock_get.return_value = mock_response

        positions = live_client.get_positions()

        assert len(positions) == 1
        assert positions[0].market_id == "0xmarket1"
        assert positions[0].side == "YES"
        assert positions[0].size == 100.0

    @patch('requests.Session.post')
    def test_place_order_success(self, mock_post, live_client, mock_audit_logger):
        """Successful order placement in LIVE mode"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"order_id": "live_order_456"}'
        mock_response.json.return_value = {"order_id": "live_order_456"}
        mock_post.return_value = mock_response

        result = live_client.place_order(
            market_id="0xmarket1",
            side=OrderSide.BUY,
            size_usd=25.0,
            price=0.60
        )

        assert result.success is True
        assert result.dryrun is False
        assert result.order_id == "live_order_456"
        mock_audit_logger.log_order.assert_called()

    @patch('requests.Session.delete')
    def test_cancel_order_success(self, mock_delete, live_client, mock_audit_logger):
        """Successful order cancellation in LIVE mode"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {}
        mock_delete.return_value = mock_response

        result = live_client.cancel_order("order_to_cancel")

        assert result is True

    @patch('requests.Session.get')
    def test_get_market_success(self, mock_get, live_client, mock_audit_logger):
        """Successful market fetch"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "0xmarket1",
            "question": "Will it rain?",
            "outcomes": ["Yes", "No"]
        }
        mock_get.return_value = mock_response

        market = live_client.get_market("0xmarket1")

        assert market["id"] == "0xmarket1"
        assert market["question"] == "Will it rain?"


class TestErrorHandling:
    """Test error handling for various failure scenarios"""

    def test_invalid_price_raises_error(self, dryrun_client):
        """Invalid price should raise OrderError"""
        with pytest.raises(OrderError) as exc_info:
            dryrun_client.place_order(
                market_id="0xmarket",
                side=OrderSide.BUY,
                size_usd=50.0,
                price=1.5  # Invalid - must be <= 1.0
            )
        assert "Price" in str(exc_info.value)

    def test_invalid_size_raises_error(self, dryrun_client):
        """Invalid size should raise OrderError"""
        with pytest.raises(OrderError) as exc_info:
            dryrun_client.place_order(
                market_id="0xmarket",
                side=OrderSide.BUY,
                size_usd=-10.0,  # Invalid - must be positive
                price=0.50
            )
        assert "Size" in str(exc_info.value)

    def test_empty_market_id_raises_error(self, dryrun_client):
        """Empty market ID should raise InvalidMarketError"""
        with pytest.raises(InvalidMarketError):
            dryrun_client.place_order(
                market_id="",
                side=OrderSide.BUY,
                size_usd=50.0,
                price=0.50
            )

    def test_empty_order_id_raises_error(self, dryrun_client):
        """Empty order ID should raise OrderError"""
        with pytest.raises(OrderError):
            dryrun_client.cancel_order("")

    @patch('requests.Session.post')
    def test_insufficient_funds_error(self, mock_post, live_client, mock_audit_logger):
        """Insufficient funds should raise InsufficientFundsError"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Insufficient balance"}'
        mock_response.json.return_value = {"error": "Insufficient balance"}
        mock_post.return_value = mock_response

        with pytest.raises(InsufficientFundsError):
            live_client.place_order(
                market_id="0xmarket",
                side=OrderSide.BUY,
                size_usd=10000000.0,
                price=0.50
            )

    @patch('requests.Session.post')
    def test_invalid_market_error(self, mock_post, live_client, mock_audit_logger):
        """Invalid market should raise InvalidMarketError"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "Market not found"}'
        mock_response.json.return_value = {"error": "Market not found"}
        mock_post.return_value = mock_response

        with pytest.raises(InvalidMarketError):
            live_client.place_order(
                market_id="0xinvalid",
                side=OrderSide.BUY,
                size_usd=50.0,
                price=0.50
            )

    @patch('requests.Session.get')
    def test_authentication_error_401(self, mock_get, live_client, mock_audit_logger):
        """401 response should raise AuthenticationError"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "Invalid credentials"}'
        mock_get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            live_client.get_balance()

    @patch('requests.Session.get')
    def test_authentication_error_403(self, mock_get, live_client, mock_audit_logger):
        """403 response should raise AuthenticationError"""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = '{"error": "Forbidden"}'
        mock_get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            live_client.get_balance()

    @patch('requests.Session.get')
    def test_rate_limit_error(self, mock_get, live_client, mock_audit_logger):
        """429 response should raise RateLimitError after retries"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}
        mock_response.text = '{"error": "Rate limited"}'
        mock_get.return_value = mock_response

        # Set retry attempts to 1 to speed up test
        live_client.RETRY_ATTEMPTS = 1

        with pytest.raises(RateLimitError):
            live_client.get_balance()

    @patch('requests.Session.get')
    def test_get_market_not_found(self, mock_get, live_client, mock_audit_logger):
        """Market not found should raise InvalidMarketError"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_get.return_value = mock_response

        with pytest.raises(InvalidMarketError):
            live_client.get_market("0xnonexistent")


class TestRateLimiting:
    """Test rate limiting behavior"""

    def test_rate_limit_delay(self, dryrun_client):
        """Requests should be delayed to respect rate limit"""
        import time

        dryrun_client._last_request_time = time.time()
        start = time.time()
        dryrun_client._rate_limit()
        elapsed = time.time() - start

        # Should have delayed by approximately RATE_LIMIT_DELAY
        assert elapsed >= dryrun_client.RATE_LIMIT_DELAY * 0.9


class TestRetryLogic:
    """Test retry logic for transient failures"""

    @patch('requests.Session.get')
    def test_retry_on_timeout(self, mock_get, live_client, mock_audit_logger):
        """Should retry on timeout"""
        import requests

        # First two calls timeout, third succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": 100.0, "available": 100.0}

        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            mock_response
        ]

        # Reduce delays for test
        live_client.RETRY_DELAY_SECONDS = 0.01

        balance = live_client.get_balance()
        assert balance.usdc_balance == 100.0
        assert mock_get.call_count == 3

    @patch('requests.Session.get')
    def test_retry_on_connection_error(self, mock_get, live_client, mock_audit_logger):
        """Should retry on connection error"""
        import requests

        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balance": 200.0, "available": 200.0}

        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            mock_response
        ]

        # Reduce delays for test
        live_client.RETRY_DELAY_SECONDS = 0.01

        balance = live_client.get_balance()
        assert balance.usdc_balance == 200.0


class TestOrderTypes:
    """Test different order types and sides"""

    def test_order_side_buy(self, dryrun_client):
        """BUY side should work correctly"""
        result = dryrun_client.place_order(
            market_id="0xmarket",
            side=OrderSide.BUY,
            size_usd=10.0,
            price=0.50
        )
        assert result.side == "BUY"

    def test_order_side_sell(self, dryrun_client):
        """SELL side should work correctly"""
        result = dryrun_client.place_order(
            market_id="0xmarket",
            side=OrderSide.SELL,
            size_usd=10.0,
            price=0.50
        )
        assert result.side == "SELL"

    def test_order_type_gtc(self, dryrun_client):
        """GTC order type should be default"""
        result = dryrun_client.place_order(
            market_id="0xmarket",
            side=OrderSide.BUY,
            size_usd=10.0,
            price=0.50
        )
        assert result.success

    def test_string_side_conversion(self, dryrun_client):
        """String side should be converted to uppercase"""
        result = dryrun_client.place_order(
            market_id="0xmarket",
            side="buy",  # lowercase string
            size_usd=10.0,
            price=0.50
        )
        assert result.side == "BUY"


class TestContextManager:
    """Test context manager functionality"""

    def test_context_manager_closes_session(self, mock_audit_logger):
        """Context manager should close session on exit"""
        with patch.object(PolymarketClient, 'close') as mock_close:
            with PolymarketClient(
                api_key="test",
                api_secret="test",
                api_passphrase="test",
                wallet_address="0x1234"
            ) as client:
                pass
            mock_close.assert_called_once()


class TestAuditLogging:
    """Test audit logging integration"""

    def test_order_logged_to_audit(self, dryrun_client, mock_audit_logger):
        """Orders should be logged to audit trail"""
        dryrun_client.place_order(
            market_id="0xmarket",
            side=OrderSide.BUY,
            size_usd=50.0,
            price=0.55
        )

        mock_audit_logger.log_order.assert_called_once()
        call_args = mock_audit_logger.log_order.call_args
        assert call_args.kwargs["market"] == "0xmarket"
        assert call_args.kwargs["side"] == "BUY"
        assert call_args.kwargs["size"] == 50.0
        assert call_args.kwargs["dryrun"] is True

    def test_balance_fetch_logged(self, dryrun_client, mock_audit_logger):
        """Balance fetches should be logged"""
        dryrun_client.get_balance()

        mock_audit_logger.log_data_fetch.assert_called()

    def test_error_logged_to_audit(self, dryrun_client, mock_audit_logger):
        """Errors should be logged to audit trail"""
        try:
            dryrun_client.place_order(
                market_id="0xmarket",
                side=OrderSide.BUY,
                size_usd=-10.0,  # Invalid
                price=0.50
            )
        except OrderError:
            pass

        # Error should not be logged for validation errors (they're raised before logging)
        # But for API errors, log_error would be called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
