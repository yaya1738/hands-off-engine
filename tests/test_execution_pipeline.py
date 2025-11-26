#!/usr/bin/env python3
"""
Integration tests for the Execution Pipeline
"""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decider.ho_decider import PlannedAction
from executor.core import ExecutorCore
from executor.pretrade import PreTradeValidator
from executor.engine import ExecutionEngine, Order, OrderStatus
from executor.posttrade import PostTradeProcessor
from executor.monitor import ExecutionMonitor


def test_pretrade_validator():
    """Test pre-trade validation checks"""
    print("Testing PreTradeValidator...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            validator = PreTradeValidator(state_dir=state_dir)
            
            # Test 1: Valid action should pass
            valid_action = PlannedAction(
                market_id='test1',
                market_name='Test Market 1',
                side='YES',
                amount=50.0,
                confidence=0.85,
                reasoning='Test valid action'
            )
            
            is_valid, results = validator.validate_trade(valid_action, bankroll=1000.0)
            assert is_valid, "Valid action should pass all checks"
            assert all(r.passed for r in results), "All checks should pass"
            
            # Test 2: Low confidence should fail
            low_conf_action = PlannedAction(
                market_id='test2',
                market_name='Test Market 2',
                side='YES',
                amount=50.0,
                confidence=0.5,
                reasoning='Test low confidence'
            )
            
            is_valid, results = validator.validate_trade(low_conf_action)
            assert not is_valid, "Low confidence should fail validation"
            
            # Test 3: Oversized position should fail
            large_action = PlannedAction(
                market_id='test3',
                market_name='Test Market 3',
                side='YES',
                amount=150.0,
                confidence=0.9,
                reasoning='Test oversized'
            )
            
            is_valid, results = validator.validate_trade(large_action)
            assert not is_valid, "Oversized position should fail validation"
            
            # Test 4: Circuit breaker
            validator.trigger_circuit_breaker("Test emergency stop")
            check = validator.check_circuit_breaker()
            assert not check.passed, "Circuit breaker should block trading"
            
            validator.reset_circuit_breaker()
            check = validator.check_circuit_breaker()
            assert check.passed, "Circuit breaker should allow trading after reset"
            
            print("✓ PreTradeValidator: PASS")
            return True
            
    except Exception as e:
        print(f"✗ PreTradeValidator: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_engine():
    """Test execution engine"""
    print("Testing ExecutionEngine...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            engine = ExecutionEngine(dryrun=True, state_dir=state_dir)
            
            # Test 1: Submit and execute order
            action = PlannedAction(
                market_id='test_market',
                market_name='Test Market',
                side='YES',
                amount=50.0,
                confidence=0.85,
                reasoning='Test execution'
            )
            
            order = engine.submit_order(action)
            assert order.order_id is not None, "Order should have ID"
            assert order.status == OrderStatus.PENDING.value, "Order should be pending"
            
            result = engine.execute_order(order)
            assert result.success, "Execution should succeed in DRYRUN"
            assert result.filled_amount == 50.0, "Should fill full amount"
            
            # Test 2: Check metrics
            metrics = engine.get_metrics()
            assert metrics['total_orders'] > 0, "Should have order count"
            assert metrics['successful_fills'] > 0, "Should have successful fills"
            
            # Test 3: Execute multiple actions
            actions = [
                PlannedAction(
                    market_id=f'test_{i}',
                    market_name=f'Test {i}',
                    side='YES' if i % 2 == 0 else 'NO',
                    amount=30.0,
                    confidence=0.8,
                    reasoning=f'Test {i}'
                )
                for i in range(3)
            ]
            
            results = engine.execute_actions(actions)
            assert len(results) == 3, "Should have result for each action"
            assert all(r.success for r in results), "All should succeed in DRYRUN"
            
            print("✓ ExecutionEngine: PASS")
            return True
            
    except Exception as e:
        print(f"✗ ExecutionEngine: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_posttrade_processor():
    """Test post-trade processing"""
    print("Testing PostTradeProcessor...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            processor = PostTradeProcessor(state_dir=state_dir)
            
            # Create test order and result
            from executor.engine import ExecutionResult
            
            order = Order(
                order_id='test_order_1',
                market_id='test_market',
                market_name='Test Market',
                side='YES',
                amount=50.0,
                price=0.6,
                status=OrderStatus.FILLED.value,
                created_at=datetime.now(timezone.utc).isoformat(),
                filled_amount=50.0,
                filled_price=0.6,
                filled_at=datetime.now(timezone.utc).isoformat()
            )
            
            result = ExecutionResult(
                order_id='test_order_1',
                success=True,
                status=OrderStatus.FILLED.value,
                filled_amount=50.0,
                filled_price=0.6,
                slippage_bps=5.0,
                execution_time_ms=150.0,
                message='Test fill'
            )
            
            # Test 1: Confirm fill
            confirmed = processor.confirm_fill(order, result)
            assert confirmed, "Fill should be confirmed"
            
            # Test 2: Update positions
            processor.update_positions(order, result)
            positions = processor.get_positions()
            assert 'test_market' in positions['positions'], "Should have position"
            
            # Test 3: Process complete execution
            processor.process_execution(order, result)
            
            # Test 4: Get position summary
            summary = processor.get_position_summary()
            assert summary['total_positions'] > 0, "Should have positions"
            assert summary['total_exposure'] > 0, "Should have exposure"
            
            print("✓ PostTradeProcessor: PASS")
            return True
            
    except Exception as e:
        print(f"✗ PostTradeProcessor: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_monitor():
    """Test execution monitoring"""
    print("Testing ExecutionMonitor...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            
            # Create engine and execute some orders first
            engine = ExecutionEngine(dryrun=True, state_dir=state_dir)
            
            actions = [
                PlannedAction(
                    market_id=f'test_{i}',
                    market_name=f'Test {i}',
                    side='YES',
                    amount=30.0,
                    confidence=0.8,
                    reasoning=f'Test {i}'
                )
                for i in range(3)
            ]
            
            engine.execute_actions(actions)
            
            # Now test monitor
            monitor = ExecutionMonitor(state_dir=state_dir)
            
            # Test 1: Check execution quality
            quality = monitor.check_execution_quality()
            assert 'metrics' in quality, "Should have metrics"
            assert 'alerts' in quality, "Should have alerts"
            assert quality['status'] in ['ok', 'warning'], "Should have valid status"
            
            # Test 2: Get pending summary
            pending = monitor.get_pending_summary()
            assert 'total_pending' in pending, "Should have pending count"
            
            # Test 3: Check timeouts (should be none for fresh orders)
            timeouts = monitor.check_timeouts()
            # Fresh orders shouldn't timeout
            
            # Test 4: Monitor loop
            summary = monitor.monitor_loop(iterations=1)
            assert 'iterations' in summary, "Should have iteration count"
            
            print("✓ ExecutionMonitor: PASS")
            return True
            
    except Exception as e:
        print(f"✗ ExecutionMonitor: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_executor_core():
    """Test complete executor core integration"""
    print("Testing ExecutorCore...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            executor = ExecutorCore(dryrun=True, state_dir=state_dir, bankroll=1000.0)
            
            # Test 1: Check status
            status = executor.get_status()
            assert status['mode'] == 'DRYRUN', "Should be in DRYRUN mode"
            assert not status['kill_switch']['enabled'], "Kill switch should be off"
            assert not status['circuit_breaker']['triggered'], "Circuit breaker should be off"
            
            # Test 2: Execute signals
            actions = [
                PlannedAction(
                    market_id='test_1',
                    market_name='Test Market 1',
                    side='YES',
                    amount=50.0,
                    confidence=0.85,
                    reasoning='Test action 1'
                ),
                PlannedAction(
                    market_id='test_2',
                    market_name='Test Market 2',
                    side='NO',
                    amount=30.0,
                    confidence=0.75,
                    reasoning='Test action 2'
                ),
            ]
            
            summary = executor.execute_signals(actions)
            assert summary['status'] == 'complete', "Execution should complete"
            assert summary['executed_count'] == 2, "Should execute both actions"
            assert summary['rejected_count'] == 0, "Should reject none"
            
            # Test 3: Kill switch
            executor.enable_kill_switch("Test emergency")
            assert executor.check_kill_switch(), "Kill switch should be enabled"
            
            # Try to execute with kill switch
            summary = executor.execute_signals(actions)
            assert summary['status'] == 'blocked', "Should be blocked by kill switch"
            
            # Disable kill switch
            executor.disable_kill_switch()
            assert not executor.check_kill_switch(), "Kill switch should be disabled"
            
            # Test 4: Reject invalid action
            invalid_action = PlannedAction(
                market_id='test_invalid',
                market_name='Invalid Test',
                side='YES',
                amount=200.0,  # Too large
                confidence=0.9,
                reasoning='Should be rejected'
            )
            
            summary = executor.execute_signals([invalid_action])
            assert summary['rejected_count'] == 1, "Should reject invalid action"
            
            print("✓ ExecutorCore: PASS")
            return True
            
    except Exception as e:
        print(f"✗ ExecutorCore: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_pipeline():
    """Test complete end-to-end execution pipeline"""
    print("Testing end-to-end execution pipeline...")
    
    try:
        from decider.ho_decider import Decider
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            
            # Use actual model file if available
            repo_root = Path(__file__).parent.parent
            model_path = repo_root / 'state' / 'polymarket-model.json'
            
            if not model_path.exists():
                print("⊘ Skipping: Model file not found")
                return True
            
            # Step 1: Load signals from Decider
            decider = Decider(bankroll=1000.0)
            signals = decider.load_model_signals(model_path)
            
            # Limit to first 3 signals for testing
            signals = signals[:3]
            
            # Step 2: Plan actions
            planned_actions = decider.plan_actions(signals)
            assert len(planned_actions) > 0, "Should have planned actions"
            
            # Step 3: Execute through pipeline
            executor = ExecutorCore(dryrun=True, state_dir=state_dir, bankroll=1000.0)
            summary = executor.execute_signals(planned_actions)
            
            assert summary['status'] == 'complete', "Pipeline should complete"
            assert summary['total_actions'] == len(planned_actions), "Should process all actions"
            
            # Step 4: Check final status
            status = executor.get_status()
            assert 'execution_quality' in status, "Should have quality metrics"
            assert 'positions' in status, "Should have position info"
            
            print("✓ End-to-end pipeline: PASS")
            return True
            
    except Exception as e:
        print(f"✗ End-to-end pipeline: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  EXECUTION PIPELINE INTEGRATION TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        test_pretrade_validator,
        test_execution_engine,
        test_posttrade_processor,
        test_execution_monitor,
        test_executor_core,
        test_end_to_end_pipeline,
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


if __name__ == '__main__':
    sys.exit(main())
