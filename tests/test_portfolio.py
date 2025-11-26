#!/usr/bin/env python3
"""
Unit tests for Portfolio Tracking System
"""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.positions import Position, PositionManager
from portfolio.tracker import PortfolioTracker
from portfolio.pnl import PnLCalculator
from portfolio.reports import ReportGenerator


def test_position_manager():
    """Test PositionManager basic operations"""
    print("Testing PositionManager...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = PositionManager(state_dir=Path(tmpdir))
        
        # Test add position
        pos = pm.add_position(
            market_id="test_market",
            market_name="Test Market",
            side="YES",
            entry_price=0.50,
            quantity=100.0,
            mode="DRYRUN"
        )
        
        assert pos.entry_amount == 50.0, "Entry amount calculation failed"
        assert pos.current_value == 50.0, "Initial value should equal entry amount"
        assert pos.status == "open", "Position should be open"
        
        # Test update price
        updated = pm.update_position_price(pos.position_id, 0.60)
        assert updated.current_price == 0.60, "Price update failed"
        assert updated.current_value == 60.0, "Value calculation failed"
        assert updated.unrealized_pnl == 10.0, "Unrealized P&L calculation failed"
        
        # Test close position
        closed = pm.close_position(pos.position_id, 0.70)
        assert closed.status == "closed", "Position should be closed"
        assert closed.realized_pnl == 20.0, "Realized P&L calculation failed"
        
        # Test get all positions
        positions = pm.get_all_positions()
        assert len(positions) == 1, "Should have 1 position"
        
        # Test filter by status
        open_positions = pm.get_all_positions(status="open")
        assert len(open_positions) == 0, "Should have no open positions"
        
        closed_positions = pm.get_all_positions(status="closed")
        assert len(closed_positions) == 1, "Should have 1 closed position"
        
        print("✓ PositionManager: PASS")
        return True


def test_portfolio_tracker():
    """Test PortfolioTracker functionality"""
    print("Testing PortfolioTracker...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = PositionManager(state_dir=Path(tmpdir))
        tracker = PortfolioTracker(position_manager=pm)
        
        # Add test positions
        pos1 = pm.add_position(
            market_id="market1",
            market_name="Market 1",
            side="YES",
            entry_price=0.50,
            quantity=100.0,
            mode="DRYRUN"
        )
        
        pos2 = pm.add_position(
            market_id="market2",
            market_name="Market 2",
            side="NO",
            entry_price=0.70,
            quantity=50.0,
            mode="DRYRUN"
        )
        
        # Test portfolio value
        total_value = tracker.get_portfolio_value(mode="DRYRUN")
        assert total_value == 85.0, f"Expected 85.0, got {total_value}"
        
        # Test cost basis
        cost_basis = tracker.get_portfolio_cost_basis(mode="DRYRUN")
        assert cost_basis == 85.0, f"Expected 85.0, got {cost_basis}"
        
        # Test position count
        count = tracker.get_position_count(mode="DRYRUN", status="open")
        assert count == 2, f"Expected 2 positions, got {count}"
        
        # Update prices
        pm.update_position_price(pos1.position_id, 0.60)
        pm.update_position_price(pos2.position_id, 0.65)
        
        # Test unrealized P&L
        unrealized = tracker.get_unrealized_pnl(mode="DRYRUN")
        assert abs(unrealized - 7.5) < 0.01, f"Expected 7.5, got {unrealized}"
        
        # Test risk limits
        allowed, msg = tracker.check_risk_limits(
            "market1", 50.0, max_per_position=100.0, mode="DRYRUN"
        )
        assert allowed, f"Should allow position: {msg}"
        
        allowed, msg = tracker.check_risk_limits(
            "market1", 150.0, max_per_position=100.0, mode="DRYRUN"
        )
        assert not allowed, "Should reject oversized position"
        
        print("✓ PortfolioTracker: PASS")
        return True


def test_pnl_calculator():
    """Test PnLCalculator functionality"""
    print("Testing PnLCalculator...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = PositionManager(state_dir=Path(tmpdir))
        calc = PnLCalculator(position_manager=pm, state_dir=Path(tmpdir))
        
        # Add and close position
        pos = pm.add_position(
            market_id="market1",
            market_name="Market 1",
            side="YES",
            entry_price=0.50,
            quantity=100.0,
            mode="DRYRUN"
        )
        pm.close_position(pos.position_id, 0.60)
        
        # Test realized P&L
        realized = calc.calculate_realized_pnl(mode="DRYRUN")
        assert realized == 10.0, f"Expected 10.0, got {realized}"
        
        # Add open position
        pos2 = pm.add_position(
            market_id="market2",
            market_name="Market 2",
            side="NO",
            entry_price=0.70,
            quantity=50.0,
            mode="DRYRUN"
        )
        pm.update_position_price(pos2.position_id, 0.75)
        
        # Test unrealized P&L
        unrealized = calc.calculate_unrealized_pnl(mode="DRYRUN")
        assert unrealized == 2.5, f"Expected 2.5, got {unrealized}"
        
        # Test total P&L
        total = calc.calculate_total_pnl(mode="DRYRUN")
        assert total == 12.5, f"Expected 12.5, got {total}"
        
        # Test P&L by market
        by_market = calc.calculate_pnl_by_market(mode="DRYRUN")
        assert "market1" in by_market, "Should have market1"
        assert by_market["market1"]["realized_pnl"] == 10.0, "Market1 realized P&L incorrect"
        
        # Test save/load daily snapshot
        calc.save_daily_snapshot(mode="DRYRUN")
        snapshots = calc.get_historical_snapshots(days=1)
        assert len(snapshots) >= 1, "Should have at least 1 snapshot"
        
        print("✓ PnLCalculator: PASS")
        return True


def test_report_generator():
    """Test ReportGenerator functionality"""
    print("Testing ReportGenerator...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = PositionManager(state_dir=Path(tmpdir))
        generator = ReportGenerator(position_manager=pm)
        
        # Add test positions
        pos = pm.add_position(
            market_id="market1",
            market_name="Market 1",
            side="YES",
            entry_price=0.50,
            quantity=100.0,
            mode="DRYRUN"
        )
        pm.update_position_price(pos.position_id, 0.60)
        
        # Test daily summary
        daily = generator.generate_daily_summary(mode="DRYRUN")
        assert "PORTFOLIO DAILY SUMMARY" in daily, "Daily summary missing header"
        assert "Open Positions: 1" in daily, "Daily summary missing position count"
        
        # Test weekly summary
        weekly = generator.generate_weekly_summary(mode="DRYRUN")
        assert "PORTFOLIO WEEKLY SUMMARY" in weekly, "Weekly summary missing header"
        
        # Test Telegram notification
        telegram = generator.get_telegram_notification_text(mode="DRYRUN")
        assert "Portfolio Update" in telegram, "Telegram text missing header"
        assert "$" in telegram, "Telegram text missing dollar signs"
        
        # Test exports
        json_path = Path(tmpdir) / "test_positions.json"
        csv_path = Path(tmpdir) / "test_positions.csv"
        pnl_path = Path(tmpdir) / "test_pnl.json"
        
        generator.export_positions_json(json_path, mode="DRYRUN")
        generator.export_positions_csv(csv_path, mode="DRYRUN")
        generator.export_pnl_json(pnl_path, mode="DRYRUN")
        
        assert json_path.exists(), "JSON export failed"
        assert csv_path.exists(), "CSV export failed"
        assert pnl_path.exists(), "P&L export failed"
        
        # Validate JSON structure
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert 'positions' in data, "JSON missing positions"
            assert len(data['positions']) == 1, "JSON wrong position count"
        
        print("✓ ReportGenerator: PASS")
        return True


def test_mode_isolation():
    """Test that DRYRUN and LIVE modes are properly isolated"""
    print("Testing mode isolation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = PositionManager(state_dir=Path(tmpdir))
        tracker = PortfolioTracker(position_manager=pm)
        
        # Add DRYRUN position
        pm.add_position(
            market_id="market1",
            market_name="Market 1",
            side="YES",
            entry_price=0.50,
            quantity=100.0,
            mode="DRYRUN"
        )
        
        # Add LIVE position
        pm.add_position(
            market_id="market2",
            market_name="Market 2",
            side="NO",
            entry_price=0.70,
            quantity=50.0,
            mode="LIVE"
        )
        
        # Test filtering
        dryrun_count = tracker.get_position_count(mode="DRYRUN")
        live_count = tracker.get_position_count(mode="LIVE")
        total_count = tracker.get_position_count()
        
        assert dryrun_count == 1, f"Expected 1 DRYRUN position, got {dryrun_count}"
        assert live_count == 1, f"Expected 1 LIVE position, got {live_count}"
        assert total_count == 2, f"Expected 2 total positions, got {total_count}"
        
        # Test portfolio value isolation
        dryrun_value = tracker.get_portfolio_value(mode="DRYRUN")
        live_value = tracker.get_portfolio_value(mode="LIVE")
        
        assert dryrun_value == 50.0, f"Expected 50.0 DRYRUN value, got {dryrun_value}"
        assert live_value == 35.0, f"Expected 35.0 LIVE value, got {live_value}"
        
        print("✓ Mode isolation: PASS")
        return True


def test_persistence():
    """Test that positions persist across sessions"""
    print("Testing persistence...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and add position
        pm1 = PositionManager(state_dir=Path(tmpdir))
        pos = pm1.add_position(
            market_id="market1",
            market_name="Market 1",
            side="YES",
            entry_price=0.50,
            quantity=100.0,
            mode="DRYRUN"
        )
        position_id = pos.position_id
        
        # Create new manager instance (simulates restart)
        pm2 = PositionManager(state_dir=Path(tmpdir))
        
        # Check position was loaded
        loaded_pos = pm2.get_position(position_id)
        assert loaded_pos is not None, "Position not loaded"
        assert loaded_pos.market_id == "market1", "Position data incorrect"
        assert loaded_pos.entry_price == 0.50, "Position price incorrect"
        
        print("✓ Persistence: PASS")
        return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  PORTFOLIO TRACKING SYSTEM TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        test_position_manager,
        test_portfolio_tracker,
        test_pnl_calculator,
        test_report_generator,
        test_mode_isolation,
        test_persistence,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__}: FAIL - {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()
    
    # Summary
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
