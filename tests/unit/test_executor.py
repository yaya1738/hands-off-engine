"""
Unit tests for executor/ho_executor_plan.py

Tests execution validation and safety checks.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decider.ho_decider import PlannedAction
from executor.ho_executor_plan import Executor, ExecutionResult


class TestExecutionResult:
    """Tests for ExecutionResult dataclass"""

    def test_execution_result_creation(self):
        """Test creating an ExecutionResult"""
        result = ExecutionResult(
            market_id="test_1",
            market_name="Test Market",
            success=True,
            message="Order placed",
            executed_amount=50.0
        )

        assert result.market_id == "test_1"
        assert result.market_name == "Test Market"
        assert result.success is True
        assert result.message == "Order placed"
        assert result.executed_amount == 50.0

    def test_execution_result_default_amount(self):
        """Test that executed_amount defaults to 0.0"""
        result = ExecutionResult(
            market_id="test_1",
            market_name="Test Market",
            success=False,
            message="Rejected"
        )

        assert result.executed_amount == 0.0


class TestExecutorInit:
    """Tests for Executor initialization"""

    def test_executor_default_dryrun(self):
        """Test Executor defaults to dryrun mode"""
        executor = Executor()
        assert executor.dryrun is True

    def test_executor_explicit_dryrun(self):
        """Test Executor with explicit dryrun setting"""
        executor = Executor(dryrun=False)
        assert executor.dryrun is False

    def test_executor_safety_parameters(self):
        """Test that safety parameters are set correctly"""
        executor = Executor()
        assert executor.MAX_POSITION_SIZE == 100.0
        assert executor.MIN_CONFIDENCE_THRESHOLD == 0.7


class TestValidateAction:
    """Tests for validate_action method"""

    def test_validate_valid_action(self):
        """Test validation of a valid action"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="YES",
            amount=50.0,
            confidence=0.85,
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is True
        assert message == "OK"

    def test_validate_low_confidence_rejected(self):
        """Test that low confidence actions are rejected"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="YES",
            amount=50.0,
            confidence=0.65,  # Below 0.7 threshold
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is False
        assert "Confidence" in message
        assert "threshold" in message

    def test_validate_oversized_position_rejected(self):
        """Test that oversized positions are rejected"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="YES",
            amount=150.0,  # Above MAX_POSITION_SIZE
            confidence=0.85,
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is False
        assert "Position size" in message or "exceeds" in message

    def test_validate_invalid_side_rejected(self):
        """Test that invalid side values are rejected"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="MAYBE",  # Invalid
            amount=50.0,
            confidence=0.85,
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is False
        assert "side" in message.lower()

    def test_validate_yes_side_accepted(self):
        """Test that YES side is accepted"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="YES",
            amount=50.0,
            confidence=0.85,
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is True

    def test_validate_no_side_accepted(self):
        """Test that NO side is accepted"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="NO",
            amount=50.0,
            confidence=0.85,
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is True

    def test_validate_boundary_confidence_accepted(self):
        """Test that confidence exactly at threshold is accepted"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="YES",
            amount=50.0,
            confidence=0.7,  # Exactly at threshold
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is True

    def test_validate_boundary_position_size_accepted(self):
        """Test that position size exactly at max is accepted"""
        executor = Executor()
        
        action = PlannedAction(
            market_id="test_1",
            market_name="Test Market",
            side="YES",
            amount=100.0,  # Exactly at MAX_POSITION_SIZE
            confidence=0.85,
            reasoning="Test"
        )

        is_valid, message = executor.validate_action(action)
        assert is_valid is True


class TestExecuteActions:
    """Tests for execute_actions method"""

    def test_execute_single_valid_action_dryrun(self):
        """Test executing a single valid action in dryrun mode"""
        executor = Executor(dryrun=True)
        
        actions = [
            PlannedAction(
                market_id="test_1",
                market_name="Test Market",
                side="YES",
                amount=50.0,
                confidence=0.85,
                reasoning="Test"
            )
        ]

        results = executor.execute_actions(actions)

        assert len(results) == 1
        result = results[0]
        assert result.success is True
        assert "DRYRUN" in result.message
        assert result.executed_amount == 50.0

    def test_execute_single_valid_action_live(self):
        """Test executing a single valid action in live mode"""
        executor = Executor(dryrun=False)
        
        actions = [
            PlannedAction(
                market_id="test_1",
                market_name="Test Market",
                side="YES",
                amount=50.0,
                confidence=0.85,
                reasoning="Test"
            )
        ]

        results = executor.execute_actions(actions)

        assert len(results) == 1
        result = results[0]
        assert result.success is True
        assert "LIVE" in result.message
        assert result.executed_amount == 50.0

    def test_execute_rejected_action(self):
        """Test executing an invalid action that gets rejected"""
        executor = Executor(dryrun=True)
        
        actions = [
            PlannedAction(
                market_id="test_1",
                market_name="Test Market",
                side="YES",
                amount=50.0,
                confidence=0.65,  # Too low
                reasoning="Test"
            )
        ]

        results = executor.execute_actions(actions)

        assert len(results) == 1
        result = results[0]
        assert result.success is False
        assert "REJECTED" in result.message
        assert result.executed_amount == 0.0

    def test_execute_multiple_actions(self):
        """Test executing multiple actions"""
        executor = Executor(dryrun=True)
        
        actions = [
            PlannedAction(
                market_id=f"test_{i}",
                market_name=f"Test Market {i}",
                side="YES",
                amount=50.0,
                confidence=0.85,
                reasoning="Test"
            )
            for i in range(3)
        ]

        results = executor.execute_actions(actions)

        assert len(results) == 3
        for result in results:
            assert result.success is True

    def test_execute_mixed_valid_invalid_actions(self):
        """Test executing mix of valid and invalid actions"""
        executor = Executor(dryrun=True)
        
        actions = [
            PlannedAction(
                market_id="test_1",
                market_name="Valid Action",
                side="YES",
                amount=50.0,
                confidence=0.85,
                reasoning="Test"
            ),
            PlannedAction(
                market_id="test_2",
                market_name="Invalid Action",
                side="YES",
                amount=150.0,  # Too large
                confidence=0.85,
                reasoning="Test"
            ),
            PlannedAction(
                market_id="test_3",
                market_name="Another Valid",
                side="NO",
                amount=75.0,
                confidence=0.90,
                reasoning="Test"
            )
        ]

        results = executor.execute_actions(actions)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    def test_execute_empty_list(self):
        """Test executing empty list of actions"""
        executor = Executor(dryrun=True)
        
        results = executor.execute_actions([])
        
        assert len(results) == 0


class TestGetExecutionSummary:
    """Tests for get_execution_summary method"""

    def test_summary_all_successful(self):
        """Test summary with all successful results"""
        executor = Executor(dryrun=True)
        
        results = [
            ExecutionResult("test_1", "Market 1", True, "Success", 50.0),
            ExecutionResult("test_2", "Market 2", True, "Success", 75.0),
        ]

        summary = executor.get_execution_summary(results)

        assert summary['total_actions'] == 2
        assert summary['successful'] == 2
        assert summary['rejected'] == 0
        assert summary['total_amount_executed'] == 125.0
        assert summary['mode'] == 'DRYRUN'

    def test_summary_all_rejected(self):
        """Test summary with all rejected results"""
        executor = Executor(dryrun=True)
        
        results = [
            ExecutionResult("test_1", "Market 1", False, "Rejected", 0.0),
            ExecutionResult("test_2", "Market 2", False, "Rejected", 0.0),
        ]

        summary = executor.get_execution_summary(results)

        assert summary['total_actions'] == 2
        assert summary['successful'] == 0
        assert summary['rejected'] == 2
        assert summary['total_amount_executed'] == 0.0

    def test_summary_mixed_results(self):
        """Test summary with mixed results"""
        executor = Executor(dryrun=True)
        
        results = [
            ExecutionResult("test_1", "Market 1", True, "Success", 50.0),
            ExecutionResult("test_2", "Market 2", False, "Rejected", 0.0),
            ExecutionResult("test_3", "Market 3", True, "Success", 75.0),
        ]

        summary = executor.get_execution_summary(results)

        assert summary['total_actions'] == 3
        assert summary['successful'] == 2
        assert summary['rejected'] == 1
        assert summary['total_amount_executed'] == 125.0

    def test_summary_live_mode(self):
        """Test summary shows LIVE mode correctly"""
        executor = Executor(dryrun=False)
        
        results = [
            ExecutionResult("test_1", "Market 1", True, "Success", 50.0),
        ]

        summary = executor.get_execution_summary(results)

        assert summary['mode'] == 'LIVE'

    def test_summary_empty_results(self):
        """Test summary with empty results list"""
        executor = Executor(dryrun=True)
        
        summary = executor.get_execution_summary([])

        assert summary['total_actions'] == 0
        assert summary['successful'] == 0
        assert summary['rejected'] == 0
        assert summary['total_amount_executed'] == 0.0


class TestSafetyReflexes:
    """Integration tests for safety reflexes"""

    def test_multiple_safety_checks(self):
        """Test that multiple safety checks work together"""
        executor = Executor(dryrun=True)
        
        # Create actions that violate different safety rules
        actions = [
            PlannedAction("t1", "Low Confidence", "YES", 50.0, 0.6, "Test"),
            PlannedAction("t2", "Large Position", "YES", 200.0, 0.9, "Test"),
            PlannedAction("t3", "Invalid Side", "MAYBE", 50.0, 0.9, "Test"),
            PlannedAction("t4", "Valid", "YES", 50.0, 0.9, "Test"),
        ]

        results = executor.execute_actions(actions)

        # All except last should be rejected
        assert results[0].success is False
        assert results[1].success is False
        assert results[2].success is False
        assert results[3].success is True


class TestBackwardsCompatibility:
    """Tests for backwards compatibility"""

    def test_execute_method_exists(self):
        """Test that legacy execute() method exists"""
        executor = Executor()
        # Should not raise
        executor.execute()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
