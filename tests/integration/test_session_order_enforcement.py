#!/usr/bin/env python3
"""
Integration Test: Agent Session Order Enforcement

Demonstrates the session order enforcement system in action.
This test creates a scenario with multiple sessions and dependencies
to show how the system prevents out-of-order execution.
"""

import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai.session_order_validator import SessionOrderValidator


def test_session_order_enforcement():
    """Test complete session order enforcement workflow"""
    
    print("\n" + "="*70)
    print("AGENT SESSION ORDER ENFORCEMENT - INTEGRATION TEST")
    print("="*70)
    
    validator = SessionOrderValidator()
    
    # Clean up any previous test sessions to ensure clean state
    state = validator.load_order_state()
    state['active_sessions'] = [s for s in state.get('active_sessions', []) 
                                 if not s['session_id'].startswith('test-')]
    state['completed_sessions'] = [s for s in state.get('completed_sessions', []) 
                                    if not s['session_id'].startswith('test-')]
    state['session_dependencies'] = {k: v for k, v in state.get('session_dependencies', {}).items() 
                                     if not k.startswith('test-')}
    validator.save_order_state(state)
    
    # Scenario: Three sessions with dependencies
    # s1 -> s2 -> s3  (linear dependency chain)
    
    print("\n📋 SCENARIO: Three sessions in linear dependency chain")
    print("   s1 (base work)")
    print("    └── s2 (depends on s1)")
    print("         └── s3 (depends on s2)")
    
    # Step 1: Try to start s3 before s1 and s2 (should fail)
    print("\n\n🔍 TEST 1: Try to start s3 before prerequisites")
    print("-" * 70)
    
    s3_can_start = validator.validate_session_order(
        session_id="test-s3-final",
        prerequisites=["test-s1-base", "test-s2-intermediate"],
        agent="copilot"
    )
    
    if not s3_can_start:
        print("✅ CORRECT: s3 blocked as expected (prerequisites not met)")
    else:
        print("❌ ERROR: s3 should have been blocked!")
        return False
    
    # Step 2: Start s1 (no prerequisites)
    print("\n\n🔍 TEST 2: Start s1 (no prerequisites)")
    print("-" * 70)
    
    s1_can_start = validator.validate_session_order(
        session_id="test-s1-base",
        prerequisites=[],
        agent="claude"
    )
    
    if s1_can_start:
        print("✅ CORRECT: s1 approved (no prerequisites)")
        validator.register_session(
            session_id="test-s1-base",
            agent="claude",
            description="Base work - no dependencies"
        )
        print("   Session registered")
    else:
        print("❌ ERROR: s1 should have been approved!")
        return False
    
    # Step 3: Try to start s2 while s1 is still running (should fail)
    print("\n\n🔍 TEST 3: Try to start s2 before s1 completes")
    print("-" * 70)
    
    s2_can_start = validator.validate_session_order(
        session_id="test-s2-intermediate",
        prerequisites=["test-s1-base"],
        agent="copilot"
    )
    
    if not s2_can_start:
        print("✅ CORRECT: s2 blocked (s1 not yet completed)")
    else:
        print("❌ ERROR: s2 should have been blocked!")
        return False
    
    # Step 4: Complete s1
    print("\n\n🔍 TEST 4: Complete s1")
    print("-" * 70)
    
    validator.complete_session(
        session_id="test-s1-base",
        outcome="success",
        notes="Base work completed successfully"
    )
    print("✅ s1 marked as completed")
    
    # Step 5: Now s2 should be able to start
    print("\n\n🔍 TEST 5: Try to start s2 after s1 completes")
    print("-" * 70)
    
    s2_can_start = validator.validate_session_order(
        session_id="test-s2-intermediate",
        prerequisites=["test-s1-base"],
        agent="copilot"
    )
    
    if s2_can_start:
        print("✅ CORRECT: s2 approved (s1 completed)")
        validator.register_session(
            session_id="test-s2-intermediate",
            agent="copilot",
            dependencies=["test-s1-base"],
            description="Intermediate work - depends on s1"
        )
        print("   Session registered")
    else:
        print("❌ ERROR: s2 should have been approved!")
        return False
    
    # Step 6: Try s3 - should still fail (s2 not complete yet)
    print("\n\n🔍 TEST 6: Try to start s3 (s1 complete, s2 running)")
    print("-" * 70)
    
    s3_can_start = validator.validate_session_order(
        session_id="test-s3-final",
        prerequisites=["test-s1-base", "test-s2-intermediate"],
        agent="chatgpt"
    )
    
    if not s3_can_start:
        print("✅ CORRECT: s3 blocked (s2 not yet completed)")
    else:
        print("❌ ERROR: s3 should have been blocked!")
        return False
    
    # Step 7: Complete s2
    print("\n\n🔍 TEST 7: Complete s2")
    print("-" * 70)
    
    validator.complete_session(
        session_id="test-s2-intermediate",
        outcome="success",
        notes="Intermediate work completed"
    )
    print("✅ s2 marked as completed")
    
    # Step 8: Now s3 should finally be able to start
    print("\n\n🔍 TEST 8: Try to start s3 (all prerequisites complete)")
    print("-" * 70)
    
    s3_can_start = validator.validate_session_order(
        session_id="test-s3-final",
        prerequisites=["test-s1-base", "test-s2-intermediate"],
        agent="chatgpt"
    )
    
    if s3_can_start:
        print("✅ CORRECT: s3 approved (all prerequisites completed)")
        validator.register_session(
            session_id="test-s3-final",
            agent="chatgpt",
            dependencies=["test-s1-base", "test-s2-intermediate"],
            description="Final work - depends on s1 and s2"
        )
        print("   Session registered")
    else:
        print("❌ ERROR: s3 should have been approved!")
        return False
    
    # Step 9: Complete s3
    print("\n\n🔍 TEST 9: Complete s3")
    print("-" * 70)
    
    validator.complete_session(
        session_id="test-s3-final",
        outcome="success",
        notes="Final work completed - all done!"
    )
    print("✅ s3 marked as completed")
    
    # Step 10: Show final status
    print("\n\n📊 FINAL STATUS:")
    print("-" * 70)
    validator.display_status()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Session order enforcement working correctly!")
    print("="*70 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        success = test_session_order_enforcement()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
