#!/usr/bin/env python3
"""
Tests for the Autonomous Trader
"""

import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.autonomous_trader import (
    AutonomousTrader,
    TradingCycleResult,
    TradingLogger,
    TelegramAlerter
)


def test_trading_logger():
    """Test that TradingLogger writes JSONL correctly."""
    print("Testing TradingLogger...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TradingLogger(Path(tmpdir))
        
        result = TradingCycleResult(
            timestamp="2025-01-01T00:00:00Z",
            cycle_number=1,
            success=True,
            error=None,
            markets_analyzed=10,
            opportunities_found=3,
            trades_executed=2,
            trades_rejected=1,
            total_amount=50.0,
            duration_seconds=1.5,
            mode="DRYRUN"
        )
        
        logger.log(result)
        
        # Verify log file exists and has correct content
        log_file = Path(tmpdir) / "trading.jsonl"
        assert log_file.exists(), "Log file should exist"
        
        with open(log_file) as f:
            logged = json.loads(f.readline())
        
        assert logged["cycle_number"] == 1
        assert logged["success"] is True
        assert logged["trades_executed"] == 2
        assert logged["total_amount"] == 50.0
        assert logged["mode"] == "DRYRUN"
        
        print("✓ TradingLogger: PASS")
        return True


def test_telegram_alerter_disabled():
    """Test TelegramAlerter when not configured."""
    print("Testing TelegramAlerter (disabled)...")
    
    # Ensure env vars are not set
    with patch.dict('os.environ', {}, clear=True):
        alerter = TelegramAlerter()
        assert not alerter.enabled, "Should be disabled without env vars"
        
        # Should not raise when calling send_alert
        alerter.send_alert("Test message")
        
        print("✓ TelegramAlerter (disabled): PASS")
        return True


def test_telegram_alerter_significant_event():
    """Test that significant events trigger alerts."""
    print("Testing TelegramAlerter significant event detection...")
    
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'TELEGRAM_CHAT_ID': 'test-chat-id'
    }):
        alerter = TelegramAlerter()
        assert alerter.enabled, "Should be enabled with env vars"
        
        # Mock the requests call
        with patch('requests.post') as mock_post:
            mock_post.return_value.raise_for_status = MagicMock()
            
            # Test with significant amount (>$10)
            result = TradingCycleResult(
                timestamp="2025-01-01T00:00:00Z",
                cycle_number=1,
                success=True,
                error=None,
                markets_analyzed=10,
                opportunities_found=3,
                trades_executed=2,
                trades_rejected=1,
                total_amount=15.0,  # > $10 threshold
                duration_seconds=1.5,
                mode="DRYRUN"
            )
            
            alerter.alert_significant_event(result)
            assert mock_post.called, "Should have sent alert for >$10 amount"
            
            mock_post.reset_mock()
            
            # Test with non-significant amount (<$10)
            result.total_amount = 5.0
            alerter.alert_significant_event(result)
            assert not mock_post.called, "Should not alert for <$10 amount"
        
        print("✓ TelegramAlerter significant event: PASS")
        return True


def test_autonomous_trader_single_cycle():
    """Test running a single trading cycle."""
    print("Testing AutonomousTrader single cycle...")
    
    trader = AutonomousTrader(
        interval=60,
        bankroll=1000.0,
        dryrun=True,
        health_port=0  # Disable health server for test
    )
    
    # Run single cycle
    result = trader.run_cycle()
    
    assert isinstance(result, TradingCycleResult)
    assert result.cycle_number == 1
    assert result.mode == "DRYRUN"
    
    # Check cycle count updated
    assert trader.cycle_count == 1
    
    print("✓ AutonomousTrader single cycle: PASS")
    return True


def test_autonomous_trader_error_recovery():
    """Test that trader handles errors gracefully."""
    print("Testing AutonomousTrader error recovery...")
    
    trader = AutonomousTrader(
        interval=60,
        bankroll=1000.0,
        dryrun=True,
        health_port=0
    )
    
    # Create a function that raises an error
    def raise_test_error():
        raise Exception("Test error")
    
    # Mock fetch_fresh_data to raise an error
    original_fetch = trader.fetch_fresh_data
    trader.fetch_fresh_data = raise_test_error
    
    # Run cycle - should not raise
    result = trader.run_cycle()
    
    assert result.success is False
    assert result.error == "Test error"
    assert trader.consecutive_errors == 1
    
    # Restore and run successful cycle
    trader.fetch_fresh_data = original_fetch
    result = trader.run_cycle()
    
    # Consecutive errors should reset on success
    assert result.success is True
    assert trader.consecutive_errors == 0
    
    print("✓ AutonomousTrader error recovery: PASS")
    return True


def test_trading_cycle_result_dataclass():
    """Test TradingCycleResult dataclass."""
    print("Testing TradingCycleResult dataclass...")
    
    result = TradingCycleResult(
        timestamp="2025-01-01T00:00:00Z",
        cycle_number=42,
        success=True,
        error=None,
        markets_analyzed=100,
        opportunities_found=10,
        trades_executed=5,
        trades_rejected=5,
        total_amount=250.0,
        duration_seconds=2.5,
        mode="LIVE"
    )
    
    # Test fields
    assert result.cycle_number == 42
    assert result.success is True
    assert result.error is None
    assert result.total_amount == 250.0
    assert result.mode == "LIVE"
    
    # Test conversion to dict
    from dataclasses import asdict
    d = asdict(result)
    assert d["cycle_number"] == 42
    assert d["mode"] == "LIVE"
    
    print("✓ TradingCycleResult dataclass: PASS")
    return True


def test_graceful_shutdown():
    """Test that trader handles shutdown signals correctly."""
    print("Testing graceful shutdown...")
    
    trader = AutonomousTrader(
        interval=1,
        bankroll=1000.0,
        dryrun=True,
        health_port=0
    )
    
    # Initially should not be running
    assert not trader.running
    
    # Simulate signal handler
    trader.running = True
    trader._signal_handler(2, None)  # SIGINT
    
    assert not trader.running
    
    print("✓ Graceful shutdown: PASS")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  AUTONOMOUS TRADER TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        test_trading_logger,
        test_telegram_alerter_disabled,
        test_telegram_alerter_significant_event,
        test_autonomous_trader_single_cycle,
        test_autonomous_trader_error_recovery,
        test_trading_cycle_result_dataclass,
        test_graceful_shutdown,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__}: FAIL - {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()
    
    # Summary
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
