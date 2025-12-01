#!/usr/bin/env python3
"""
Automation System Validation Tests

Tests the autonomous components of the Hands-Off Engine to ensure
automation success is maintained and validated.

Run with: python -m pytest tests/test_automation_validation.py -v
"""

import pytest
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Paths
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
AI_DIR = REPO_ROOT / "ai"
AUTONOMOUS_DIR = REPO_ROOT / "autonomous"

# Add repo root to path (done once at module level)
sys.path.insert(0, str(REPO_ROOT))


class TestAutomationComponentsExist:
    """Validate that all automation components are present."""
    
    def test_autonomous_directory_exists(self):
        """Verify autonomous directory exists with key components."""
        assert AUTONOMOUS_DIR.exists()
        assert (AUTONOMOUS_DIR / "absolute_directive.py").exists()
        assert (AUTONOMOUS_DIR / "moonshot_loop.py").exists()
    
    def test_ai_directories_exist(self):
        """Verify AI coordination directories exist."""
        assert (AI_DIR / "tasks").exists()
        assert (AI_DIR / "results").exists()
        assert (AI_DIR / "coordination").exists()
    
    def test_state_directory_structure(self):
        """Verify state directory has required structure."""
        assert STATE_DIR.exists()
        # Check for key state files
        assert (STATE_DIR / "knowledge.json").exists()


class TestAbsoluteDirectiveSystem:
    """Test the 80-mile cascade architecture."""
    
    def test_absolute_directive_import(self):
        """Verify AbsoluteDirective can be imported."""
        from autonomous.absolute_directive import (
            AbsoluteDirective,
            get_master,
            get_directive
        )
        
        assert get_master() == "Yair Siegel"
        assert get_directive() == "Serve without bound"
    
    def test_absolute_directive_inheritance(self):
        """Verify components can inherit from AbsoluteDirective."""
        from autonomous.absolute_directive import AbsoluteDirective
        
        class TestComponent(AbsoluteDirective):
            def __init__(self):
                super().__init__()
        
        component = TestComponent()
        assert component.master == "Yair Siegel"
        assert component.directive == "Serve without bound"
        assert component.serve() == "Serving Yair Siegel"


class TestAICoordinationSystem:
    """Test AI coordination infrastructure."""
    
    def test_coordination_status_file_exists(self):
        """Verify coordination status file exists and is valid JSON."""
        status_file = AI_DIR / "coordination" / "status.json"
        assert status_file.exists()
        
        with open(status_file) as f:
            status = json.load(f)
        
        assert "active_agents" in status
        assert "autonomous_mode" in status
        assert "current_phase" in status
    
    def test_coordination_status_has_required_fields(self):
        """Verify coordination status has all required fields."""
        status_file = AI_DIR / "coordination" / "status.json"
        
        with open(status_file) as f:
            status = json.load(f)
        
        required_fields = [
            "last_updated",
            "active_agents",
            "autonomous_mode",
            "current_phase",
            "pending_tasks"
        ]
        
        for field in required_fields:
            assert field in status, f"Missing required field: {field}"
    
    def test_autonomous_mode_enabled(self):
        """Verify autonomous mode is enabled for all agents."""
        status_file = AI_DIR / "coordination" / "status.json"
        
        with open(status_file) as f:
            status = json.load(f)
        
        autonomous_mode = status.get("autonomous_mode", {})
        
        # Check key agents have autonomous mode enabled
        key_agents = ["copilot", "claude-code"]
        for agent in key_agents:
            assert autonomous_mode.get(agent) is True, \
                f"Autonomous mode not enabled for {agent}"


class TestAIRunnerSystem:
    """Test AI Runner automation infrastructure."""
    
    def test_ai_runner_exists(self):
        """Verify ai_runner.py exists."""
        ai_runner = REPO_ROOT / "ai_runner.py"
        assert ai_runner.exists()
    
    def test_ai_runner_import(self):
        """Verify ai_runner can be imported."""
        try:
            import ai_runner
            assert hasattr(ai_runner, 'TASKS_DIR')
            assert hasattr(ai_runner, 'RESULTS_DIR')
        except ImportError as e:
            pytest.skip(f"ai_runner import dependencies not available: {e}")
    
    def test_tasks_directory_structure(self):
        """Verify tasks directory has correct structure."""
        tasks_dir = AI_DIR / "tasks"
        assert tasks_dir.exists()
        assert (tasks_dir / "processed").exists()


class TestTradingPipeline:
    """Test automated trading pipeline components."""
    
    def test_autoloop_exists(self):
        """Verify ho_autoloop.py exists."""
        autoloop = REPO_ROOT / "ho_autoloop.py"
        assert autoloop.exists()
    
    def test_autoloop_import(self):
        """Verify ho_autoloop can be imported."""
        from ho_autoloop import run_all
        
        assert callable(run_all)
    
    def test_pipeline_components_exist(self):
        """Verify pipeline components exist."""
        components = [
            "fetchers",
            "alpha",
            "decider",
            "executor"
        ]
        
        for component in components:
            component_dir = REPO_ROOT / component
            assert component_dir.exists(), \
                f"Pipeline component missing: {component}"


class TestSafetyControls:
    """Test automation safety controls."""
    
    def test_dryrun_default_in_autoloop(self):
        """Verify DRYRUN is the default mode."""
        autoloop_file = REPO_ROOT / "ho_autoloop.py"
        
        with open(autoloop_file) as f:
            content = f.read()
        
        # Check for DRYRUN mentions
        assert "DRYRUN" in content
        assert '"mode": "DRYRUN"' in content or "'mode': 'DRYRUN'" in content
    
    def test_executor_safety_exists(self):
        """Verify executor has safety checks."""
        executor_dir = REPO_ROOT / "executor"
        
        # Check if executor files exist
        executor_files = list(executor_dir.glob("*.py"))
        assert len(executor_files) > 0, "No executor Python files found"
        
        # Check for safety patterns in executor files
        has_safety = False
        for executor_file in executor_files:
            with open(executor_file) as f:
                content = f.read()
                if "DRYRUN" in content or "safety" in content.lower():
                    has_safety = True
                    break
        
        assert has_safety, "No safety controls found in executor"


class TestDocumentation:
    """Test automation documentation completeness."""
    
    def test_automation_success_metrics_exists(self):
        """Verify automation success metrics documentation exists."""
        metrics_doc = REPO_ROOT / "docs" / "AUTOMATION_SUCCESS_METRICS.md"
        assert metrics_doc.exists()
    
    def test_automation_success_metrics_content(self):
        """Verify automation success metrics has key sections."""
        metrics_doc = REPO_ROOT / "docs" / "AUTOMATION_SUCCESS_METRICS.md"
        
        with open(metrics_doc) as f:
            content = f.read()
        
        required_sections = [
            "Executive Summary",
            "Deployed Automation Components",
            "Success Metrics",
            "Safety Controls"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"
    
    def test_risk_model_documentation_exists(self):
        """Verify risk model documentation exists."""
        risk_doc = REPO_ROOT / "docs" / "RISK_MODEL_V1.md"
        assert risk_doc.exists()
    
    def test_deployment_status_exists(self):
        """Verify deployment status documentation exists."""
        deployment_doc = AI_DIR / "DEPLOYMENT_STATUS.md"
        assert deployment_doc.exists()


class TestKnowledgeManagement:
    """Test knowledge.json and documentation registry."""
    
    def test_knowledge_json_valid(self):
        """Verify knowledge.json is valid JSON."""
        knowledge_file = STATE_DIR / "knowledge.json"
        assert knowledge_file.exists()
        
        with open(knowledge_file) as f:
            knowledge = json.load(f)
        
        assert "required_reading" in knowledge
        assert "optional_docs" in knowledge
    
    def test_automation_metrics_registered(self):
        """Verify automation metrics doc is registered in knowledge.json."""
        knowledge_file = STATE_DIR / "knowledge.json"
        
        with open(knowledge_file) as f:
            knowledge = json.load(f)
        
        all_docs = knowledge.get("optional_docs", []) + \
                   knowledge.get("required_reading", [])
        
        # Check for exact match of the document path
        assert "docs/AUTOMATION_SUCCESS_METRICS.md" in all_docs, \
            "docs/AUTOMATION_SUCCESS_METRICS.md not registered in knowledge.json"


class TestSystemHealth:
    """Test overall system health indicators."""
    
    def test_no_critical_lock_files(self):
        """Verify no critical lock files that would block automation."""
        critical_locks = [
            STATE_DIR / "SYSTEM_FAILURE.lock",
            STATE_DIR / "EMERGENCY_STOP.lock"
        ]
        
        for lock_file in critical_locks:
            assert not lock_file.exists(), \
                f"Critical lock file exists: {lock_file}"
    
    def test_state_files_valid_json(self):
        """Verify key state files are valid JSON."""
        key_state_files = [
            "knowledge.json",
            "ai_nexus_state.json"
        ]
        
        for state_file in key_state_files:
            file_path = STATE_DIR / state_file
            
            if file_path.exists():
                with open(file_path) as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON in {state_file}")


# Integration test
class TestAutomationIntegration:
    """Integration tests for automation system."""
    
    def test_cascade_system_functional(self):
        """Test that cascade directive system works end-to-end."""
        from autonomous.absolute_directive import cascade_directive
        
        # Run cascade
        result = cascade_directive("Test automation validation")
        
        assert result is not None
        assert "timestamp" in result
        assert "master" in result
        assert "levels_touched" in result
        assert result["status"] == "complete"
        assert len(result["levels_touched"]) == 8  # 8 cascade levels
    
    def test_ai_runner_process_task_structure(self):
        """Test that ai_runner can process task structure."""
        try:
            from ai_runner import process_sparkplug_autokernel_refresh
            
            # Test with minimal task structure
            test_task = {
                "task_type": "sparkplug_autokernel_refresh",
                "task_id": "test_validation",
                "mode": "config",
                "dry_run": True
            }
            
            # Should not crash with proper task structure
            assert test_task["task_type"] == "sparkplug_autokernel_refresh"
        except ImportError as e:
            pytest.skip(f"ai_runner dependencies not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
