#!/usr/bin/env python3
"""
Tests for Claude Audit Integration

Tests the Claude Code CLI audit logging system.
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit import AuditLogger, FinancialLedger
from ai_nexus import ClaudeProvider


def test_claude_provider_integration():
    """Test that ClaudeProvider integrates with audit system"""
    print("Testing ClaudeProvider integration...")
    
    # Create temporary audit directory
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_logger = AuditLogger(log_dir=tmpdir)
        ledger_file = Path(tmpdir) / "test_ledger.jsonl"
        ledger = FinancialLedger(ledger_file=str(ledger_file))
        
        # Create provider
        claude = ClaudeProvider(audit_logger, ledger)
        
        # Log an action
        claude.log_action(
            action="test_action",
            files_changed=2,
            lines_added=50,
            lines_removed=20,
            metadata={"test": True}
        )
        
        # Verify audit log
        events = audit_logger.get_events(component="ai.claude")
        assert len(events) == 1, f"Expected 1 event, got {len(events)}"
        
        event = events[0]
        assert event.action == "test_action", f"Expected action 'test_action', got '{event.action}'"
        assert event.metadata.get("files_changed") == 2, f"Expected files_changed=2, got {event.metadata.get('files_changed')}"
        assert event.metadata.get("lines_added") == 50, f"Expected lines_added=50, got {event.metadata.get('lines_added')}"
        assert event.metadata.get("lines_removed") == 20, f"Expected lines_removed=20, got {event.metadata.get('lines_removed')}"
        assert event.cost is not None and event.cost > 0, f"Cost should be calculated, got {event.cost}"
        
        # Verify ledger
        ledger_entries = ledger.get_entries(component="ai.claude")
        assert len(ledger_entries) == 1, f"Expected 1 ledger entry, got {len(ledger_entries)}"
        
        entry = ledger_entries[0]
        assert entry.action == "test_action", f"Expected action 'test_action', got '{entry.action}'"
        assert entry.category == "cost", f"Expected category 'cost', got '{entry.category}'"
        # Costs are stored as negative in the ledger
        assert entry.amount != 0, f"Expected non-zero amount, got {entry.amount}"
        
    print("✅ ClaudeProvider integration test passed")


def test_cost_estimation():
    """Test that cost estimation works correctly"""
    print("Testing cost estimation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_logger = AuditLogger(log_dir=tmpdir)
        ledger_file = Path(tmpdir) / "test_ledger.jsonl"
        ledger = FinancialLedger(ledger_file=str(ledger_file))
        claude = ClaudeProvider(audit_logger, ledger)
        
        # Test with known values
        claude.log_action(
            action="test_cost",
            files_changed=1,
            lines_added=100,
            lines_removed=50,
            tokens_used=1000  # Provide explicit token count
        )
        
        # Get the logged cost
        events = audit_logger.get_events(component="ai.claude")
        cost = events[0].cost
        
        # Verify cost is reasonable (should be small for 1000 tokens)
        assert cost > 0, "Cost should be positive"
        assert cost < 1.0, f"Cost should be less than $1 for 1000 tokens, got ${cost}"
        
    print("✅ Cost estimation test passed")


def test_session_tracking():
    """Test that sessions are tracked correctly"""
    print("Testing session tracking...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_logger = AuditLogger(log_dir=tmpdir)
        ledger_file = Path(tmpdir) / "test_ledger.jsonl"
        ledger = FinancialLedger(ledger_file=str(ledger_file))
        claude = ClaudeProvider(audit_logger, ledger)
        
        session_id = audit_logger.session_id
        
        # Log multiple actions in same session
        for i in range(3):
            claude.log_action(
                action=f"test_action_{i}",
                files_changed=1,
                lines_added=10
            )
        
        # Verify all events have same session
        events = audit_logger.get_events(session_id=session_id)
        assert len(events) == 3, f"Expected 3 events in session, got {len(events)}"
        
        for event in events:
            assert event.session_id == session_id
        
        # Get session summary
        summary = audit_logger.get_session_summary(session_id)
        assert summary["total_events"] == 3
        assert summary["total_cost"] > 0
        assert "ai.claude" in summary["component_stats"]
        
    print("✅ Session tracking test passed")


def test_metadata_tracking():
    """Test that metadata is properly tracked"""
    print("Testing metadata tracking...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_logger = AuditLogger(log_dir=tmpdir)
        ledger_file = Path(tmpdir) / "test_ledger.jsonl"
        ledger = FinancialLedger(ledger_file=str(ledger_file))
        claude = ClaudeProvider(audit_logger, ledger)
        
        # Log with rich metadata
        test_metadata = {
            "pr_number": 42,
            "feature": "audit_system",
            "priority": "high"
        }
        
        claude.log_action(
            action="code_review",
            files_changed=5,
            lines_added=100,
            lines_removed=50,
            metadata=test_metadata
        )
        
        # Verify metadata is preserved
        events = audit_logger.get_events(component="ai.claude")
        event_metadata = events[0].metadata
        
        assert event_metadata["pr_number"] == 42
        assert event_metadata["feature"] == "audit_system"
        assert event_metadata["priority"] == "high"
        assert event_metadata["files_changed"] == 5
        assert event_metadata["lines_added"] == 100
        assert event_metadata["lines_removed"] == 50
        
    print("✅ Metadata tracking test passed")


def test_ledger_integrity():
    """Test that ledger maintains integrity"""
    print("Testing ledger integrity...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_file = Path(tmpdir) / "test_ledger.jsonl"
        ledger = FinancialLedger(ledger_file=str(ledger_file))
        
        # Add multiple entries
        for i in range(5):
            ledger.add_cost(
                component="ai.claude",
                action=f"action_{i}",
                amount=0.1 * i,
                session_id="test_session",
                metadata={"index": i}
            )
        
        # Verify integrity
        assert ledger.verify_integrity(), "Ledger integrity check failed"
        
    print("✅ Ledger integrity test passed")


def run_all_tests():
    """Run all tests"""
    print("="*80)
    print("Running Claude Audit Integration Tests")
    print("="*80)
    print()
    
    tests = [
        test_claude_provider_integration,
        test_cost_estimation,
        test_session_tracking,
        test_metadata_tracking,
        test_ledger_integrity
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1
            print()
    
    print("="*80)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
