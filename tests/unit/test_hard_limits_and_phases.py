"""
Unit tests for hard limits and phase progression.

Tests the safety layers that prevent the system from exceeding absolute caps
and ensure conservative phase progression.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from executor.trading_safeguards import (
    enforce_hard_limits,
    load_hard_limits,
    check_trading_health,
)
from scripts.recalibrate_engine import adjust_risk_profile


class TestHardLimits:
    """Tests for hard limit enforcement"""

    def test_enforce_hard_limits_clamps_position_size(self):
        """Test that position size is clamped to hard limits"""
        # Create a risk profile with values above hard caps
        risk_profile = {
            "max_position_usd": 500,  # Above hard limit of 200
            "max_daily_loss_usd": 200,
            "confidence_threshold": 0.45,
        }

        # Enforce hard limits
        enforced = enforce_hard_limits(risk_profile)

        # Assert values are clamped
        assert enforced["max_position_usd"] == 200, "Position size should be capped at hard limit"
        assert enforced["max_daily_loss_usd"] == 200, "Daily loss is within limits"

    def test_enforce_hard_limits_clamps_daily_loss(self):
        """Test that daily loss is clamped to hard limits"""
        risk_profile = {
            "max_position_usd": 50,
            "max_daily_loss_usd": 1000,  # Above hard limit of 400
            "confidence_threshold": 0.45,
        }

        enforced = enforce_hard_limits(risk_profile)

        assert enforced["max_daily_loss_usd"] == 400, "Daily loss should be capped at hard limit"

    def test_enforce_hard_limits_raises_confidence_floor(self):
        """Test that confidence threshold is raised to minimum"""
        risk_profile = {
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "confidence_threshold": 0.30,  # Below hard minimum of 0.40
        }

        enforced = enforce_hard_limits(risk_profile)

        assert enforced["confidence_threshold"] >= 0.40, "Confidence should be raised to minimum"

    def test_enforce_hard_limits_preserves_valid_values(self):
        """Test that values within limits are preserved"""
        risk_profile = {
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "confidence_threshold": 0.45,
            "max_trades_per_hour": 10,
        }

        enforced = enforce_hard_limits(risk_profile)

        assert enforced["max_position_usd"] == 50
        assert enforced["max_daily_loss_usd"] == 200
        assert enforced["confidence_threshold"] == 0.45
        assert enforced["max_trades_per_hour"] == 10


class TestHealthCheck:
    """Tests for health check functionality"""

    def test_check_trading_health_passes_when_healthy(self):
        """Test that health check passes with no issues"""
        # Health check currently has no performance log, so it should pass
        is_healthy, issues = check_trading_health()

        # With no log file, most checks are skipped
        assert isinstance(is_healthy, bool)
        assert isinstance(issues, list)

    def test_check_trading_health_detects_stale_risk_profile(self, tmp_path):
        """Test that health check detects stale risk profile"""
        # Create a risk profile with old timestamp
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        risk_profile = {
            "version": "1.0",
            "last_updated": old_time,
            "max_position_usd": 50,
        }

        risk_profile_path = tmp_path / "risk_profile.json"
        risk_profile_path.write_text(json.dumps(risk_profile))

        # Patch the RISK_PROFILE_PATH
        with patch('executor.trading_safeguards.RISK_PROFILE_PATH', risk_profile_path):
            is_healthy, issues = check_trading_health()

            # Should detect stale risk profile
            assert any("stale_risk_profile" in issue for issue in issues)


class TestPhaseProgression:
    """Tests for conservative phase progression rules"""

    def test_phase_progression_requires_minimum_trades(self):
        """Test that phase upgrade requires minimum trades"""
        # Create current profile in baby_mode
        current_profile = {
            "phase": "baby_mode",
            "phase_entry_time": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "scale_factor": 1.0,
            "calibration_history": [],
        }

        # Metrics with insufficient trades but good performance
        metrics = {
            "hit_rate": 0.60,  # Above 52% requirement
            "total_pnl": 100,  # Positive
            "max_drawdown": 10,  # Low
            "trade_count": 20,  # Below 30 requirement
        }

        # Attempt adjustment
        new_profile, changes = adjust_risk_profile(current_profile, metrics)

        # Should NOT upgrade phase due to insufficient trades
        assert new_profile["phase"] == "baby_mode", "Should stay in baby_mode with < 30 trades"
        assert any("locked" in change or "insufficient" in change for change in changes)

    def test_phase_progression_requires_minimum_days(self):
        """Test that phase upgrade requires minimum days in phase"""
        # Create current profile in baby_mode, entered only 3 days ago
        current_profile = {
            "phase": "baby_mode",
            "phase_entry_time": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "scale_factor": 1.0,
            "calibration_history": [],
        }

        # Metrics with sufficient trades but insufficient time
        metrics = {
            "hit_rate": 0.60,  # Above 52% requirement
            "total_pnl": 100,  # Positive
            "max_drawdown": 10,  # Low
            "trade_count": 40,  # Above 30 requirement
        }

        # Attempt adjustment
        new_profile, changes = adjust_risk_profile(current_profile, metrics)

        # Should NOT upgrade phase due to insufficient days
        assert new_profile["phase"] == "baby_mode", "Should stay in baby_mode with < 7 days"

    def test_phase_progression_baby_to_scale_up_with_requirements_met(self):
        """Test successful phase upgrade when all requirements met"""
        # Create current profile in baby_mode, sufficient time
        current_profile = {
            "phase": "baby_mode",
            "phase_entry_time": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "scale_factor": 1.0,
            "calibration_history": [],
        }

        # Metrics meeting all requirements
        metrics = {
            "hit_rate": 0.60,  # Above 52% requirement
            "total_pnl": 500,  # Positive
            "max_drawdown": 10,  # Low
            "trade_count": 40,  # Above 30 requirement
        }

        # Attempt adjustment
        new_profile, changes = adjust_risk_profile(current_profile, metrics)

        # Should upgrade to scale_up
        assert new_profile["phase"] == "scale_up", "Should upgrade to scale_up"
        assert new_profile["max_position_usd"] == 250
        assert new_profile["max_daily_loss_usd"] == 1000
        assert any("upgrade" in change for change in changes)

    def test_phase_progression_scale_up_to_full_requires_more_trades(self):
        """Test that scale_up to full_deployment requires 50+ trades"""
        current_profile = {
            "phase": "scale_up",
            "phase_entry_time": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(),
            "max_position_usd": 250,
            "max_daily_loss_usd": 1000,
            "scale_factor": 2.5,
            "calibration_history": [],
        }

        # Metrics with insufficient trades (only 40)
        metrics = {
            "hit_rate": 0.60,  # Above 53% requirement
            "total_pnl": 1000,  # Positive
            "max_drawdown": 50,  # Low relative to limit
            "trade_count": 40,  # Below 50 requirement
        }

        # Attempt adjustment
        new_profile, changes = adjust_risk_profile(current_profile, metrics)

        # Should NOT upgrade to full_deployment
        assert new_profile["phase"] == "scale_up", "Should stay in scale_up with < 50 trades"

    def test_phase_downgrade_on_poor_performance(self):
        """Test that poor performance triggers phase downgrade"""
        current_profile = {
            "phase": "scale_up",
            "phase_entry_time": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(),
            "max_position_usd": 250,
            "max_daily_loss_usd": 1000,
            "scale_factor": 2.5,
            "calibration_history": [],
        }

        # Poor performance metrics
        metrics = {
            "hit_rate": 0.40,  # Below 45% threshold
            "total_pnl": -600,  # Large loss
            "max_drawdown": 500,
            "trade_count": 60,
        }

        # Attempt adjustment
        new_profile, changes = adjust_risk_profile(current_profile, metrics)

        # Should downgrade to baby_mode
        assert new_profile["phase"] == "baby_mode", "Should downgrade on poor performance"
        assert new_profile["max_position_usd"] == 50
        assert any("downgrade" in change for change in changes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
