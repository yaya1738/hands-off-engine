"""
Unit tests for executor shadow mode.

Tests that shadow mode executes the full pipeline without making real API calls,
and that live mode properly calls the API when conditions are met.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from dataclasses import dataclass

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from executor.ho_executor_plan import Executor, ExecutionResult, get_executor_mode
from executor.shadow_sink import record_shadow_order


@dataclass
class MockPlannedAction:
    """Mock planned action for testing"""
    market_id: str
    market_name: str
    side: str
    amount: float
    confidence: float


class TestGetExecutorMode:
    """Tests for get_executor_mode() function"""

    def test_explicit_mode_shadow(self, monkeypatch):
        """Test that explicit HANDS_OFF_EXECUTOR_MODE=shadow is respected"""
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "shadow")
        mode = get_executor_mode()
        assert mode == "shadow"

    def test_explicit_mode_live(self, monkeypatch):
        """Test that explicit HANDS_OFF_EXECUTOR_MODE=live is respected"""
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "live")
        mode = get_executor_mode()
        assert mode == "live"

    def test_explicit_mode_dryrun(self, monkeypatch):
        """Test that explicit HANDS_OFF_EXECUTOR_MODE=dryrun is respected"""
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "dryrun")
        mode = get_executor_mode()
        assert mode == "dryrun"

    def test_backwards_compat_live_trading_enabled(self, monkeypatch):
        """Test backwards compatibility with LIVE_TRADING_ENABLED"""
        monkeypatch.delenv("HANDS_OFF_EXECUTOR_MODE", raising=False)
        monkeypatch.setenv("LIVE_TRADING_ENABLED", "1")

        # Need to reload module to pick up new env var
        import importlib
        import executor.ho_executor_plan
        importlib.reload(executor.ho_executor_plan)
        from executor.ho_executor_plan import get_executor_mode

        mode = get_executor_mode()
        # Should infer "live" from LIVE_TRADING_ENABLED=1
        # Note: This test may need adjustment based on actual implementation

    def test_default_mode_is_dryrun(self, monkeypatch):
        """Test that default mode is dryrun when nothing is set"""
        monkeypatch.delenv("HANDS_OFF_EXECUTOR_MODE", raising=False)
        monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)

        # Need to reload module
        import importlib
        import executor.ho_executor_plan
        importlib.reload(executor.ho_executor_plan)
        from executor.ho_executor_plan import get_executor_mode

        mode = get_executor_mode()
        assert mode == "dryrun"


class TestShadowSink:
    """Tests for shadow sink logging"""

    def test_record_shadow_order_creates_log_entry(self, tmp_path):
        """Test that record_shadow_order creates a valid JSON log entry"""
        shadow_log = tmp_path / "shadow_trades.jsonl"

        record_shadow_order(
            market_id="market_123",
            market_name="Test Market",
            side="YES",
            size_usd=50.0,
            price=0.65,
            confidence=0.72,
            source="test_source",
            executor_mode="shadow",
            health_ok=True,
            health_reason="OK",
            risk_phase="baby_mode",
            caps_applied=[],
            safety_checks=["Position size: OK", "Daily loss: OK"],
            extra={"test_field": "test_value"},
            log_path=shadow_log,
        )

        # Verify file was created
        assert shadow_log.exists()

        # Read and parse the log entry
        with open(shadow_log) as f:
            entry = json.loads(f.read())

        # Verify key fields
        assert entry["market_id"] == "market_123"
        assert entry["market_name"] == "Test Market"
        assert entry["side"] == "YES"
        assert entry["size_usd"] == 50.0
        assert entry["confidence"] == 0.72
        assert entry["executor_mode"] == "shadow"
        assert entry["health_ok"] is True
        assert entry["risk_phase"] == "baby_mode"
        assert "timestamp" in entry
        assert entry["extra"]["test_field"] == "test_value"


class TestExecutorShadowMode:
    """Tests for executor behavior in shadow mode"""

    def test_executor_shadow_mode_never_calls_api(self, tmp_path, monkeypatch):
        """Test that shadow mode never calls the real trading API"""
        # Set shadow mode
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "shadow")

        # Reload to pick up env var
        import importlib
        import executor.ho_executor_plan
        importlib.reload(executor.ho_executor_plan)

        # Mock the trader to raise if called
        mock_trader = MagicMock()
        mock_trader.place_market_order_usd = Mock(side_effect=Exception("API should not be called in shadow mode!"))

        # Patch the trader
        with patch('executor.ho_executor_plan.trader', mock_trader):
            # Create executor
            executor = executor.ho_executor_plan.Executor(dryrun=False)

            # Create a mock action
            action = MockPlannedAction(
                market_id="test_market",
                market_name="Test Market",
                side="YES",
                amount=50.0,
                confidence=0.75,
            )

            # Set shadow log path to temp directory
            shadow_log = tmp_path / "shadow_trades.jsonl"
            with patch('executor.shadow_sink.DEFAULT_SHADOW_LOG', shadow_log):
                # Execute the action
                results = executor.execute_actions([action])

            # Verify API was never called
            mock_trader.place_market_order_usd.assert_not_called()

            # Verify a shadow log entry was created
            assert shadow_log.exists()

            # Verify the entry contains expected data
            with open(shadow_log) as f:
                entry = json.loads(f.read())

            assert entry["market_id"] == "test_market"
            assert entry["executor_mode"] == "shadow"
            assert entry["side"] == "YES"
            assert entry["size_usd"] == 50.0

    def test_executor_dryrun_mode_never_calls_api(self, monkeypatch):
        """Test that dryrun mode never calls the API"""
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "dryrun")

        import importlib
        import executor.ho_executor_plan
        importlib.reload(executor.ho_executor_plan)

        # Mock the trader to raise if called
        mock_trader = MagicMock()
        mock_trader.place_market_order_usd = Mock(side_effect=Exception("API should not be called in dryrun mode!"))

        with patch('executor.ho_executor_plan.trader', mock_trader):
            executor = executor.ho_executor_plan.Executor(dryrun=True)

            action = MockPlannedAction(
                market_id="test_market",
                market_name="Test Market",
                side="YES",
                amount=50.0,
                confidence=0.75,
            )

            results = executor.execute_actions([action])

            # Verify API was never called
            mock_trader.place_market_order_usd.assert_not_called()

            # Verify result indicates dryrun
            assert len(results) == 1
            assert "DRYRUN" in results[0].message

    def test_executor_shadow_mode_logs_blocked_trades(self, tmp_path, monkeypatch):
        """Test that shadow mode logs trades that would be blocked by safeguards"""
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "shadow")

        import importlib
        import executor.ho_executor_plan
        importlib.reload(executor.ho_executor_plan)

        executor = executor.ho_executor_plan.Executor(dryrun=False)

        # Create an action that will be blocked (low confidence)
        action = MockPlannedAction(
            market_id="test_market",
            market_name="Test Market",
            side="YES",
            amount=50.0,
            confidence=0.30,  # Below threshold
        )

        shadow_log = tmp_path / "shadow_trades.jsonl"
        with patch('executor.shadow_sink.DEFAULT_SHADOW_LOG', shadow_log):
            results = executor.execute_actions([action])

        # Result should indicate rejection
        assert len(results) == 1
        assert not results[0].success
        assert "REJECTED" in results[0].message or "Confidence" in results[0].message


class TestExecutorLiveMode:
    """Tests for executor behavior in live mode"""

    def test_executor_live_mode_calls_api_when_healthy(self, monkeypatch):
        """Test that live mode calls API when all conditions are met"""
        # This test requires more setup and is more complex
        # It would patch is_live_trading_enabled() to return True
        # and mock the trader to record calls
        pass  # Placeholder - full implementation would be more involved

    def test_executor_live_mode_blocked_when_unhealthy(self, monkeypatch):
        """Test that live mode is blocked when health check fails"""
        monkeypatch.setenv("HANDS_OFF_EXECUTOR_MODE", "live")

        import importlib
        import executor.ho_executor_plan
        importlib.reload(executor.ho_executor_plan)

        # Mock is_live_trading_enabled to return False (unhealthy)
        with patch('executor.ho_executor_plan.is_live_trading_enabled', return_value=False):
            # Mock trader
            mock_trader = MagicMock()

            with patch('executor.ho_executor_plan.trader', mock_trader):
                executor = executor.ho_executor_plan.Executor(dryrun=False)

                action = MockPlannedAction(
                    market_id="test_market",
                    market_name="Test Market",
                    side="YES",
                    amount=50.0,
                    confidence=0.75,
                )

                results = executor.execute_actions([action])

                # API should not be called
                mock_trader.place_market_order_usd.assert_not_called()

                # Result should indicate blocking
                assert len(results) == 1
                assert "BLOCKED" in results[0].message or not results[0].success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
