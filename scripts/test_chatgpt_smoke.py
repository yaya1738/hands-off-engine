#!/usr/bin/env python3
"""
Simple ChatGPT Integration Smoke Test
No external dependencies required - just run with python3
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_import():
    """Test that ChatGPTAdapter can be imported"""
    print("Test 1: Import ChatGPTAdapter")
    try:
        from ai.integration import ChatGPTAdapter
        print("  ✓ Import successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_initialization():
    """Test adapter initialization"""
    print("\nTest 2: Initialize adapter")
    try:
        from ai.integration import ChatGPTAdapter
        adapter = ChatGPTAdapter()
        print(f"  ✓ Adapter initialized")
        print(f"    - Agent ID: {adapter.agent_id}")
        print(f"    - Model: {adapter.model}")
        print(f"    - API Key configured: {adapter.api_key is not None}")
        return True
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return False


def test_no_api_key_handling():
    """Test graceful handling when no API key"""
    print("\nTest 3: No API key error handling")
    try:
        from ai.integration import ChatGPTAdapter
        
        # Temporarily clear API key
        old_key = os.environ.get("OPENAI_API_KEY")
        if old_key:
            del os.environ["OPENAI_API_KEY"]
        
        adapter = ChatGPTAdapter()
        result = adapter.send_query("test")
        
        # Restore key
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        
        if result["success"] is False and "No OpenAI API key" in result["error"]:
            print("  ✓ Graceful error handling works")
            print(f"    - Error message: {result['error']}")
            return True
        else:
            print(f"  ✗ Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        # Restore key on exception
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        return False


def test_mega_system_integration():
    """Test integration with mega unified system"""
    print("\nTest 4: Mega Unified System integration")
    try:
        from ai.mega_unified_system import get_mega_system
        system = get_mega_system()
        state = system.get_full_state()
        
        if "chatgpt" in state.get("component_status", {}):
            status = state["component_status"]["chatgpt"]
            print(f"  ✓ ChatGPT registered in mega system")
            print(f"    - Status: {status}")
            return True
        else:
            print("  ✗ ChatGPT not found in component status")
            return False
            
    except ImportError as e:
        print(f"  ⊘ Mega system not available (skip): {e}")
        return True  # Don't fail on optional dependency
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_api_call_if_configured():
    """Test actual API call if key is configured"""
    print("\nTest 5: API call (if configured)")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("  ⊘ Skipped (no API key configured)")
        return True
    
    try:
        from ai.integration import ChatGPTAdapter
        adapter = ChatGPTAdapter()
        
        print("  → Sending test query to OpenAI...")
        result = adapter.send_query("What is 2+2? Answer with just the number.")
        
        if result["success"]:
            print(f"  ✓ API call successful")
            print(f"    - Response: {result['response'][:100]}")
            print(f"    - Tokens: {result.get('tokens_used', {})}")
            return True
        else:
            print(f"  ✗ API call failed")
            print(f"    - Error: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ChatGPT Integration Smoke Test")
    print("=" * 60)
    
    tests = [
        test_import,
        test_initialization,
        test_no_api_key_handling,
        test_mega_system_integration,
        test_api_call_if_configured,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\nUnexpected error in {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        failed = [tests[i].__name__ for i, r in enumerate(results) if not r]
        print(f"\n✗ Some tests failed: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
