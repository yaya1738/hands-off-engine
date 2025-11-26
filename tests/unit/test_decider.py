"""
Unit tests for decider/ho_decider.py

Tests the decision logic and Kelly sizing functionality.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decider.ho_decider import Decider, PlannedAction


class TestPlannedAction:
    """Tests for PlannedAction dataclass"""

    def test_planned_action_creation(self):
        """Test creating a PlannedAction"""
        action = PlannedAction(
            market_id="test_market_1",
            market_name="Test Market",
            side="YES",
            amount=50.0,
            confidence=0.85,
            reasoning="Edge: 5.0%, Current odds: 0.50, Confidence: 85.0%"
        )

        assert action.market_id == "test_market_1"
        assert action.market_name == "Test Market"
        assert action.side == "YES"
        assert action.amount == 50.0
        assert action.confidence == 0.85
        assert "Edge" in action.reasoning


class TestDeciderInit:
    """Tests for Decider initialization"""

    def test_decider_default_bankroll(self):
        """Test Decider with default bankroll"""
        decider = Decider()
        assert decider.bankroll == 1000.0

    def test_decider_custom_bankroll(self):
        """Test Decider with custom bankroll"""
        decider = Decider(bankroll=5000.0)
        assert decider.bankroll == 5000.0


class TestLoadModelSignals:
    """Tests for load_model_signals method"""

    def test_load_model_signals_valid_file(self, tmp_path):
        """Test loading valid model signals file"""
        # Create test model file
        model_data = {
            "generated_at": "2025-01-15T12:00:00Z",
            "markets": [
                {
                    "market_id": "test_1",
                    "question": "Test question?",
                    "side": "YES",
                    "model_edge": 0.05,
                    "model_confidence": 0.75,
                    "fair_price": 0.55,
                    "market_price": 0.50
                }
            ]
        }

        model_path = tmp_path / "test_model.json"
        with open(model_path, 'w') as f:
            json.dump(model_data, f)

        decider = Decider()
        signals = decider.load_model_signals(model_path)

        assert len(signals) == 1
        assert signals[0]['market_id'] == "test_1"
        assert signals[0]['market_name'] == "Test question?"
        assert signals[0]['edge'] == 0.05
        assert signals[0]['side'] == "YES"
        assert signals[0]['model_confidence'] == 0.75

    def test_load_model_signals_multiple_markets(self, tmp_path):
        """Test loading multiple markets from model file"""
        model_data = {
            "markets": [
                {
                    "market_id": f"market_{i}",
                    "question": f"Question {i}?",
                    "side": "YES" if i % 2 == 0 else "NO",
                    "model_edge": 0.05 + (i * 0.01),
                    "model_confidence": 0.70 + (i * 0.02),
                    "fair_price": 0.50,
                    "market_price": 0.45
                }
                for i in range(5)
            ]
        }

        model_path = tmp_path / "test_model.json"
        with open(model_path, 'w') as f:
            json.dump(model_data, f)

        decider = Decider()
        signals = decider.load_model_signals(model_path)

        assert len(signals) == 5
        for i, signal in enumerate(signals):
            assert signal['market_id'] == f"market_{i}"
            assert signal['edge'] == 0.05 + (i * 0.01)


class TestPlanActions:
    """Tests for plan_actions method"""

    def test_plan_actions_single_signal(self):
        """Test planning actions from single signal"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.05,
            'current_odds': 0.50,
            'side': 'YES',
            'model_confidence': 0.75
        }]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        assert len(actions) == 1
        action = actions[0]
        assert action.market_id == 'test_1'
        assert action.side == 'YES'
        assert action.confidence == 0.75
        assert action.amount > 0
        assert action.amount <= 100  # Max 10% of bankroll

    def test_plan_actions_kelly_sizing(self):
        """Test Kelly criterion sizing calculation"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.10,  # 10% edge
            'current_odds': 0.50,
            'side': 'YES',
            'model_confidence': 0.80  # 80% confidence
        }]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        action = actions[0]
        # Kelly fraction = edge * confidence = 0.10 * 0.80 = 0.08
        # Expected amount = 1000 * 0.08 = 80
        assert action.amount == pytest.approx(80.0, rel=0.01)

    def test_plan_actions_caps_at_max_fraction(self):
        """Test that position size is capped at 10% of bankroll"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.50,  # Very high edge
            'current_odds': 0.50,
            'side': 'YES',
            'model_confidence': 0.90  # High confidence
        }]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        action = actions[0]
        # Should be capped at 10% = $100
        assert action.amount <= 100.0
        assert action.amount == 100.0

    def test_plan_actions_uses_default_confidence(self):
        """Test that default confidence is derived from edge when not provided"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.05,
            'current_odds': 0.50,
            'side': 'YES',
            # No model_confidence provided
        }]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        action = actions[0]
        # Confidence should be 0.5 + (0.05 * 5) = 0.75
        assert action.confidence == pytest.approx(0.75, rel=0.01)

    def test_plan_actions_clamps_confidence(self):
        """Test that confidence is clamped to [0, 1] range"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.50,  # Very high edge
            'current_odds': 0.50,
            'side': 'YES',
            # No model_confidence - would calculate > 1.0
        }]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        action = actions[0]
        # Should be clamped at 1.0
        assert action.confidence <= 1.0

    def test_plan_actions_multiple_signals(self):
        """Test planning actions for multiple signals"""
        decider = Decider(bankroll=1000.0)
        
        signals = [
            {
                'market_id': f'market_{i}',
                'market_name': f'Market {i}',
                'edge': 0.05,
                'current_odds': 0.50,
                'side': 'YES',
                'model_confidence': 0.75
            }
            for i in range(3)
        ]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        assert len(actions) == 3
        for i, action in enumerate(actions):
            assert action.market_id == f'market_{i}'

    def test_plan_actions_reasoning_format(self):
        """Test that reasoning string is properly formatted"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.05,
            'current_odds': 0.50,
            'side': 'YES',
            'model_confidence': 0.75
        }]

        with patch('decider.ho_decider.log_kernel_history_event'):
            actions = decider.plan_actions(signals)

        action = actions[0]
        assert "Edge: 5.0%" in action.reasoning
        assert "Current odds: 0.50" in action.reasoning
        assert "Confidence: 75.0%" in action.reasoning


class TestHistoryLogging:
    """Tests for history logging integration"""

    @patch('decider.ho_decider.log_kernel_history_event')
    def test_logs_risk_decisions(self, mock_log):
        """Test that risk decisions are logged for each signal"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.05,
            'current_odds': 0.50,
            'side': 'YES',
            'model_confidence': 0.75
        }]

        actions = decider.plan_actions(signals)

        # Should log risk decision + aggregate outcome = 2 calls
        assert mock_log.call_count == 2

    @patch('decider.ho_decider.log_kernel_history_event')
    def test_logs_aggregate_outcome(self, mock_log):
        """Test that aggregate outcome is logged"""
        decider = Decider(bankroll=1000.0)
        
        signals = [
            {
                'market_id': f'market_{i}',
                'market_name': f'Market {i}',
                'edge': 0.05,
                'current_odds': 0.50,
                'side': 'YES' if i % 2 == 0 else 'NO',
                'model_confidence': 0.75
            }
            for i in range(3)
        ]

        actions = decider.plan_actions(signals)

        # Last call should be aggregate outcome
        last_call = mock_log.call_args_list[-1]
        assert last_call[1]['kind'] == 'decider_outcome'
        assert last_call[1]['source'] == 'ho_decider'
        assert 'num_decisions' in last_call[1]['details']
        assert last_call[1]['details']['num_decisions'] == 3

    @patch('decider.ho_decider.log_kernel_history_event', side_effect=Exception("Log error"))
    def test_logging_errors_dont_crash(self, mock_log):
        """Test that logging errors don't crash the decider"""
        decider = Decider(bankroll=1000.0)
        
        signals = [{
            'market_id': 'test_1',
            'market_name': 'Test Market',
            'edge': 0.05,
            'current_odds': 0.50,
            'side': 'YES',
            'model_confidence': 0.75
        }]

        # Should not raise exception despite logging error
        actions = decider.plan_actions(signals)
        assert len(actions) == 1


class TestBackwardsCompatibility:
    """Tests for backwards compatibility"""

    def test_decide_method_exists(self):
        """Test that legacy decide() method exists"""
        decider = Decider()
        # Should not raise
        decider.decide()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
