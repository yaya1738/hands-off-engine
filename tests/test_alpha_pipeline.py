#!/usr/bin/env python3
"""
Integration tests for the Polymarket Alpha Pipeline
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.sync_polymarket_model import sync_polymarket_model
from decider.ho_decider import Decider
from executor.ho_executor_plan import Executor


def test_sync_polymarket_model():
    """Test that sync_polymarket_model generates valid output"""
    print("Testing sync_polymarket_model...")
    
    # Paths
    repo_root = Path(__file__).parent.parent
    input_path = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
    
    if not input_path.exists():
        print(f"⊘ Skipping: Input file not found at {input_path}")
        return True
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        # Run sync
        model = sync_polymarket_model(input_path, output_path, max_markets=10)
        
        # Validate output
        assert 'generated_at' in model, "Model missing 'generated_at'"
        assert 'markets' in model, "Model missing 'markets'"
        assert isinstance(model['markets'], list), "Markets should be a list"
        assert len(model['markets']) > 0, "Should have at least one market"
        
        # Validate market structure
        market = model['markets'][0]
        required_fields = [
            'market_id', 'question', 'side', 'model_edge',
            'model_confidence', 'fair_price', 'market_price'
        ]
        for field in required_fields:
            assert field in market, f"Market missing required field: {field}"
        
        # Validate value ranges
        assert 0.0 <= market['model_edge'] <= 1.0, "Edge should be in [0, 1]"
        assert 0.0 <= market['model_confidence'] <= 1.0, "Confidence should be in [0, 1]"
        assert market['side'] in ['YES', 'NO'], "Side should be YES or NO"
        
        print("✓ sync_polymarket_model: PASS")
        return True
        
    finally:
        # Clean up temp file
        if output_path.exists():
            output_path.unlink()


def test_decider_load_model():
    """Test that Decider can load and process model file"""
    print("Testing Decider.load_model_signals...")
    
    repo_root = Path(__file__).parent.parent
    model_path = repo_root / 'state' / 'polymarket-model.json'
    
    if not model_path.exists():
        print(f"⊘ Skipping: Model file not found at {model_path}")
        return True
    
    try:
        decider = Decider(bankroll=1000.0)
        signals = decider.load_model_signals(model_path)
        
        # Validate signals
        assert isinstance(signals, list), "Signals should be a list"
        assert len(signals) > 0, "Should have at least one signal"
        
        # Validate signal structure
        signal = signals[0]
        required_fields = [
            'market_id', 'market_name', 'edge', 'current_odds',
            'side', 'model_confidence'
        ]
        for field in required_fields:
            assert field in signal, f"Signal missing required field: {field}"
        
        print("✓ Decider.load_model_signals: PASS")
        return True
        
    except Exception as e:
        print(f"✗ Decider.load_model_signals: FAIL - {e}")
        return False


def test_end_to_end_pipeline():
    """Test end-to-end pipeline: model → decider → executor"""
    print("Testing end-to-end pipeline...")
    
    repo_root = Path(__file__).parent.parent
    model_path = repo_root / 'state' / 'polymarket-model.json'
    
    if not model_path.exists():
        print(f"⊘ Skipping: Model file not found at {model_path}")
        return True
    
    try:
        # Load signals
        decider = Decider(bankroll=1000.0)
        signals = decider.load_model_signals(model_path)
        
        # Plan actions
        planned_actions = decider.plan_actions(signals)
        assert isinstance(planned_actions, list), "Should return list of actions"
        assert len(planned_actions) > 0, "Should have at least one action"
        
        # Execute actions
        executor = Executor(dryrun=True)
        results = executor.execute_actions(planned_actions)
        assert isinstance(results, list), "Should return list of results"
        assert len(results) == len(planned_actions), "Should have result for each action"
        
        # Get summary
        summary = executor.get_execution_summary(results)
        assert summary['mode'] == 'DRYRUN', "Should be in DRYRUN mode"
        assert summary['total_actions'] == len(planned_actions), "Total count mismatch"
        
        print("✓ End-to-end pipeline: PASS")
        return True
        
    except Exception as e:
        print(f"✗ End-to-end pipeline: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_executor_safety_reflexes():
    """Test that executor safety reflexes work correctly"""
    print("Testing executor safety reflexes...")
    
    try:
        from decider.ho_decider import PlannedAction
        
        executor = Executor(dryrun=True)
        
        # Test 1: Low confidence should be rejected
        low_conf_action = PlannedAction(
            market_id='test1',
            market_name='Test Market 1',
            side='YES',
            amount=50.0,
            confidence=0.5,  # Below 0.7 threshold
            reasoning='Test'
        )
        
        is_valid, msg = executor.validate_action(low_conf_action)
        assert not is_valid, "Low confidence should be rejected"
        assert 'Confidence' in msg, "Error message should mention confidence"
        
        # Test 2: Oversized position should be rejected
        large_action = PlannedAction(
            market_id='test2',
            market_name='Test Market 2',
            side='YES',
            amount=150.0,  # Above MAX_POSITION_SIZE
            confidence=0.9,
            reasoning='Test'
        )
        
        is_valid, msg = executor.validate_action(large_action)
        assert not is_valid, "Oversized position should be rejected"
        assert 'Position size' in msg or 'exceeds' in msg, "Error message should mention size"
        
        # Test 3: Invalid side should be rejected
        invalid_side_action = PlannedAction(
            market_id='test3',
            market_name='Test Market 3',
            side='MAYBE',  # Invalid
            amount=50.0,
            confidence=0.9,
            reasoning='Test'
        )
        
        is_valid, msg = executor.validate_action(invalid_side_action)
        assert not is_valid, "Invalid side should be rejected"
        assert 'side' in msg.lower(), "Error message should mention side"
        
        # Test 4: Valid action should pass
        valid_action = PlannedAction(
            market_id='test4',
            market_name='Test Market 4',
            side='YES',
            amount=50.0,
            confidence=0.9,
            reasoning='Test'
        )
        
        is_valid, msg = executor.validate_action(valid_action)
        assert is_valid, f"Valid action should pass: {msg}"
        
        print("✓ Executor safety reflexes: PASS")
        return True
        
    except Exception as e:
        print(f"✗ Executor safety reflexes: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  ALPHA PIPELINE INTEGRATION TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        test_sync_polymarket_model,
        test_decider_load_model,
        test_end_to_end_pipeline,
        test_executor_safety_reflexes,
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
