"""Regression tests for the legacy executor's dry-run and fail-closed behavior."""

import json
import math
from dataclasses import dataclass

from executor.ho_executor_plan import Executor
from executor.shadow_sink import record_shadow_order


@dataclass
class MockPlannedAction:
    market_id: str
    market_name: str
    side: str
    amount: float
    confidence: float


class TestShadowSink:
    def test_record_shadow_order_creates_log_entry(self, tmp_path):
        shadow_log = tmp_path / "shadow_trades.jsonl"
        record_shadow_order(
            market_id="market_123",
            market_name="Test Market",
            side="YES",
            size_usd=50.0,
            price=0.65,
            confidence=0.72,
            source="test_source",
            executor_mode="shadow",
            health_ok=True,
            health_reason="OK",
            risk_phase="baby_mode",
            caps_applied=[],
            safety_checks=["Position size: OK"],
            extra={"test_field": "test_value"},
            log_path=shadow_log,
        )

        assert shadow_log.exists()
        entry = json.loads(shadow_log.read_text())
        assert entry["market_id"] == "market_123"
        assert entry["executor_mode"] == "shadow"
        assert entry["extra"]["test_field"] == "test_value"


class TestExecutor:
    def action(self, amount=50.0, confidence=0.75):
        return MockPlannedAction(
            market_id="test_market",
            market_name="Test Market",
            side="YES",
            amount=amount,
            confidence=confidence,
        )

    def test_dryrun_never_calls_live_api_and_is_explicitly_simulated(self):
        executor = Executor.__new__(Executor)
        executor.dryrun = True

        result = executor.execute_actions([self.action()])[0]

        assert result.success is True
        assert "DRYRUN" in result.message
        assert result.executed_amount > 0

    def test_live_mode_is_blocked_without_governed_adapter(self):
        executor = Executor.__new__(Executor)
        executor.dryrun = False

        result = executor.execute_actions([self.action()])[0]

        assert result.success is False
        assert result.executed_amount == 0.0
        assert "no governed live execution adapter" in result.message

    def test_low_confidence_action_is_rejected(self):
        executor = Executor.__new__(Executor)
        executor.dryrun = True

        result = executor.execute_actions([self.action(confidence=0.30)])[0]

        assert result.success is False
        assert "REJECTED" in result.message

    def test_invalid_amounts_are_rejected(self):
        executor = Executor.__new__(Executor)
        executor.dryrun = True

        for amount in (0, -1, math.nan, math.inf, -math.inf):
            result = executor.execute_actions([self.action(amount=amount)])[0]
            assert result.success is False
            assert result.executed_amount == 0.0
