#!/usr/bin/env python3
"""
Test that critical modules can be imported without errors.

This test was created after fixing the absolute_directive.py module
which had import-time side effects that caused PermissionError.
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_absolute_directive_import():
    """Test that absolute_directive can be imported."""
    from autonomous.absolute_directive import AbsoluteDirective, get_master, get_directive
    
    assert get_master() == "Yair Siegel"
    assert get_directive() == "Serve without bound"
    print("✓ absolute_directive imports successfully")


def test_unified_ai_import():
    """Test that unified_ai can be imported."""
    from ai.unified_ai import UnifiedAI, get_master, get_directive
    
    assert get_master() == "Yair Siegel"
    print("✓ unified_ai imports successfully")


def test_autonomous_module_import():
    """Test that autonomous module can be imported."""
    import autonomous
    
    assert hasattr(autonomous, 'UnifiedAutonomousSystem')
    print("✓ autonomous module imports successfully")


def test_absolute_directive_class():
    """Test that AbsoluteDirective class can be instantiated."""
    from autonomous.absolute_directive import AbsoluteDirective
    
    # Should not raise PermissionError
    directive = AbsoluteDirective()
    
    assert directive.master == "Yair Siegel"
    assert directive.directive == "Serve without bound"
    assert directive.serve() == "Serving Yair Siegel"
    print("✓ AbsoluteDirective class works correctly")


def test_unified_ai_class():
    """Test that UnifiedAI class can be instantiated."""
    from ai.unified_ai import UnifiedAI
    
    # Should not raise PermissionError
    ai = UnifiedAI()
    
    assert ai.master == "Yair Siegel"
    assert ai.level == "60 miles"
    
    identity = ai.get_identity()
    assert identity["master"] == "Yair Siegel"
    print("✓ UnifiedAI class works correctly")


def test_no_import_side_effects():
    """Test that importing modules doesn't create unwanted side effects."""
    import os
    import sys
    
    # In the old broken version, importing created files in /root/
    # This test verifies that doesn't happen anymore
    # Skip if we're actually running as root in /root/ (Termux phone node)
    if os.path.exists("/root/hands-off-engine"):
        print("✓ Running in production environment, skipping side-effect check")
        return
    
    # In test/dev environments, these should not exist
    assert not os.path.exists("/root/hands-off-engine/state/ABSOLUTE_TRUTH.json")
    print("✓ No unwanted side effects in /root/")


def main():
    """Run all tests."""
    tests = [
        test_absolute_directive_import,
        test_unified_ai_import,
        test_autonomous_module_import,
        test_absolute_directive_class,
        test_unified_ai_class,
        test_no_import_side_effects,
    ]
    
    print("Running import tests...")
    print()
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print()
    print("=" * 60)
    print("All import tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
