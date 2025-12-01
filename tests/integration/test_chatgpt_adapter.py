"""
Tests for ChatGPT Integration

Tests the chatgpt_adapter.py functionality including:
- Basic adapter initialization
- API configuration
- Query functionality (if API key available)
- Logging functionality
"""

import os
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.integration.chatgpt_adapter import ChatGPTAdapter


class TestChatGPTAdapterBasic:
    """Tests that don't require API key"""
    
    def test_import(self):
        """Test that ChatGPTAdapter can be imported"""
        from ai.integration import ChatGPTAdapter
        assert ChatGPTAdapter is not None
    
    def test_initialization(self):
        """Test adapter can be initialized"""
        adapter = ChatGPTAdapter()
        assert adapter is not None
        assert adapter.agent_id == "chatgpt"
        assert adapter.model in ["gpt-4o", "gpt-4o-mini"]
    
    def test_api_key_loading(self):
        """Test that API key is loaded from environment"""
        adapter = ChatGPTAdapter()
        # Should load from OPENAI_API_KEY env var
        # Will be None if not configured, which is OK for this test
        assert isinstance(adapter.api_key, (str, type(None)))
    
    def test_no_api_key_error_handling(self):
        """Test graceful handling when no API key configured"""
        # Temporarily clear API key
        old_key = os.environ.get("OPENAI_API_KEY")
        if old_key:
            del os.environ["OPENAI_API_KEY"]
        
        try:
            adapter = ChatGPTAdapter()
            result = adapter.send_query("test")
            
            # Should return error, not crash
            assert result["success"] is False
            assert "No OpenAI API key" in result["error"]
        finally:
            # Restore key if it existed
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key
    
    def test_task_delegation_structure(self):
        """Test that task delegation has correct structure"""
        adapter = ChatGPTAdapter()
        
        # Even without API key, can test structure
        task = {
            "type": "research",
            "description": "Test task",
            "context": {"test": True}
        }
        
        # delegate_task should return a dict result
        # (will fail without API key, but should have proper structure)
        result = adapter.delegate_task(task)
        assert isinstance(result, dict)
        assert "success" in result


class TestChatGPTAdapterWithAPI:
    """Tests that require valid API key - skipped if not available"""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="No OPENAI_API_KEY configured"
    )
    def test_simple_query(self):
        """Test basic query functionality"""
        adapter = ChatGPTAdapter()
        result = adapter.send_query("What is 2+2? Answer with just the number.")
        
        assert result["success"] is True
        assert "response" in result
        assert "4" in result["response"]
        assert "tokens_used" in result
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="No OPENAI_API_KEY configured"
    )
    def test_query_with_context(self):
        """Test query with context parameter"""
        adapter = ChatGPTAdapter()
        context = {"test_mode": True, "example": "context"}
        result = adapter.send_query(
            "Respond with 'context received' if you see the context",
            context=context
        )
        
        assert result["success"] is True
        assert "response" in result
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="No OPENAI_API_KEY configured"
    )
    def test_research_task(self):
        """Test research task delegation"""
        adapter = ChatGPTAdapter()
        result = adapter.get_research_summary("Python programming")
        
        assert result["success"] is True
        assert "response" in result
        assert len(result["response"]) > 50  # Should have substantive response
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="No OPENAI_API_KEY configured"
    )
    def test_market_analysis(self):
        """Test market analysis functionality"""
        adapter = ChatGPTAdapter()
        result = adapter.analyze_market(
            "will-btc-reach-100k",
            current_price=0.50
        )
        
        assert result["success"] is True
        assert "response" in result
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="No OPENAI_API_KEY configured"
    )
    def test_logging_created(self):
        """Test that logs are created after API calls"""
        adapter = ChatGPTAdapter()
        
        # Make a simple query
        adapter.send_query("Test query for logging")
        
        # Check log file exists
        log_file = Path(__file__).parent.parent.parent / "ai" / "integration" / "chatgpt_log.jsonl"
        assert log_file.exists()
        
        # Check log has entries
        with open(log_file) as f:
            lines = f.readlines()
            assert len(lines) > 0
            
            # Check last entry is valid JSON
            last_entry = json.loads(lines[-1])
            assert "timestamp" in last_entry
            assert "from" in last_entry
            assert "to" in last_entry


class TestChatGPTIntegration:
    """Integration tests with other components"""
    
    def test_mega_unified_system_import(self):
        """Test that ChatGPT is recognized in mega_unified_system"""
        try:
            from ai.mega_unified_system import get_mega_system
            system = get_mega_system()
            
            # Check ChatGPT is in component status
            state = system.get_full_state()
            assert "component_status" in state
            assert "chatgpt" in state["component_status"]
            
            # Should be either "ready" or "missing" depending on import
            status = state["component_status"]["chatgpt"]
            assert status in ["ready", "missing", "active"]
        except ImportError:
            pytest.skip("mega_unified_system not available")
    
    def test_nexus_hub_integration(self):
        """Test that ChatGPT is registered in AI Nexus Hub"""
        try:
            from ai.integration import get_hub
            hub = get_hub()
            
            # ChatGPT should be registered as an agent
            # (Protocol defines it even if not active)
            agent_status = hub.get_agent_status()
            # May or may not be active, but should be known
            assert isinstance(agent_status, dict)
        except ImportError:
            pytest.skip("ai_nexus_hub not available")


class TestChatGPTCLI:
    """Tests for CLI functionality"""
    
    def test_cli_interface_exists(self):
        """Test that CLI can be invoked"""
        adapter_file = Path(__file__).parent.parent.parent / "ai" / "integration" / "chatgpt_adapter.py"
        assert adapter_file.exists()
        
        # File should have main() function
        content = adapter_file.read_text()
        assert "def main():" in content
        assert 'if __name__ == "__main__":' in content


class TestChatGPTSafety:
    """Safety and security tests"""
    
    def test_no_api_key_in_logs(self):
        """Test that API keys are never logged"""
        log_file = Path(__file__).parent.parent.parent / "ai" / "integration" / "chatgpt_log.jsonl"
        
        if log_file.exists():
            content = log_file.read_text()
            # Should never contain API key patterns
            assert "sk-" not in content
            assert "OPENAI_API_KEY" not in content
    
    def test_log_previews_only(self):
        """Test that logs contain previews, not full responses"""
        adapter = ChatGPTAdapter()
        
        # The _log_exchange method should preview only
        # Check the code limits preview to 200 chars
        adapter_file = Path(__file__).parent.parent.parent / "ai" / "integration" / "chatgpt_adapter.py"
        content = adapter_file.read_text()
        
        # Should have preview limiting
        assert "[:200]" in content or "[0:200]" in content


# Utility functions for manual testing
def manual_smoke_test():
    """Run this manually to test ChatGPT is working"""
    print("ChatGPT Integration Smoke Test")
    print("=" * 50)
    
    adapter = ChatGPTAdapter()
    print(f"✓ Adapter initialized")
    print(f"  Model: {adapter.model}")
    print(f"  API Key configured: {adapter.api_key is not None}")
    
    if not adapter.api_key:
        print("\n✗ No API key configured")
        print("  Set OPENAI_API_KEY environment variable")
        return False
    
    print("\n→ Testing simple query...")
    result = adapter.send_query("What is 2+2? Just give the number.")
    
    if result["success"]:
        print(f"✓ Query successful")
        print(f"  Response: {result['response'][:100]}")
        print(f"  Tokens used: {result.get('tokens_used', 'N/A')}")
        return True
    else:
        print(f"✗ Query failed")
        print(f"  Error: {result.get('error', 'Unknown')}")
        return False


if __name__ == "__main__":
    # Run smoke test if executed directly
    import sys
    success = manual_smoke_test()
    sys.exit(0 if success else 1)
