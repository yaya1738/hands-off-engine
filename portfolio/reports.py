"""
Report Generator for Hands-Off Engine

Generates human-readable reports for portfolio performance:
- Daily summary reports
- Weekly performance reports
- Export functions for analysis (JSON/CSV)
"""

import json
import csv
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger
from portfolio.positions import PositionManager
from portfolio.tracker import PortfolioTracker
from portfolio.pnl import PnLCalculator


class ReportGenerator:
    """
    Generates reports for portfolio tracking and P&L analysis.
    Supports multiple output formats and time periods.
    """
    
    def __init__(self, position_manager: Optional[PositionManager] = None):
        """
        Initialize report generator.
        
        Args:
            position_manager: PositionManager instance (creates new if None)
        """
        self.position_manager = position_manager or PositionManager()
        self.tracker = PortfolioTracker(position_manager=self.position_manager)
        self.pnl_calc = PnLCalculator(position_manager=self.position_manager)
        self.audit = get_audit_logger(component="report_generator")
    
    def generate_daily_summary(self, mode: Optional[str] = None) -> str:
        """
        Generate daily summary report as formatted text.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Formatted text report
        """
        summary = self.tracker.get_portfolio_summary(mode=mode)
        pnl_report = self.pnl_calc.get_pnl_report(mode=mode)
        health = self.tracker.get_portfolio_health_check(mode=mode)
        
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        mode_str = mode or "ALL MODES"
        
        lines = [
            "=" * 70,
            f"PORTFOLIO DAILY SUMMARY - {today}",
            f"Mode: {mode_str}",
            "=" * 70,
            "",
            "PORTFOLIO STATUS:",
            f"  Open Positions: {summary['open_positions']['count']}",
            f"  Total Value: ${summary['open_positions']['total_value']:.2f}",
            f"  Total Cost: ${summary['open_positions']['total_cost']:.2f}",
            f"  Unrealized P&L: ${summary['open_positions']['unrealized_pnl']:.2f} ({summary['open_positions']['unrealized_pnl_pct']:.2f}%)",
            "",
            "CLOSED POSITIONS:",
            f"  Count: {summary['closed_positions']['count']}",
            f"  Realized P&L: ${summary['closed_positions']['realized_pnl']:.2f}",
            "",
            "TOTAL P&L:",
            f"  ${summary['total_pnl']:.2f}",
            "",
        ]
        
        # Add market breakdown
        if pnl_report['by_market']:
            lines.append("P&L BY MARKET:")
            for market_id, data in sorted(pnl_report['by_market'].items(),
                                         key=lambda x: x[1]['total_pnl'],
                                         reverse=True):
                market_name = data.get('market_name', market_id)[:50]
                lines.append(f"  {market_name}")
                lines.append(f"    Total P&L: ${data['total_pnl']:.2f}")
                lines.append(f"    Open: {data['open_positions']}, Closed: {data['closed_positions']}")
            lines.append("")
        
        # Add health check warnings
        lines.append("HEALTH CHECK:")
        lines.append(f"  Status: {health['status']}")
        if health['warnings']:
            lines.append("  Warnings:")
            for warning in health['warnings']:
                lines.append(f"    - {warning}")
        else:
            lines.append("  No warnings")
        lines.append("")
        
        lines.append("=" * 70)
        
        report_text = "\n".join(lines)
        
        # Log report generation
        self.audit.log_action(
            action_type="daily_summary_generated",
            action_data={'mode': mode or "ALL"},
            result="success"
        )
        
        return report_text
    
    def generate_weekly_summary(self, mode: Optional[str] = None) -> str:
        """
        Generate weekly performance report as formatted text.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Formatted text report
        """
        today = datetime.now(timezone.utc)
        week_start = today - timedelta(days=7)
        
        # Get current portfolio state
        summary = self.tracker.get_portfolio_summary(mode=mode)
        
        # Get P&L for the week
        weekly_realized = self.pnl_calc.calculate_realized_pnl(
            mode=mode,
            start_date=week_start,
            end_date=today
        )
        
        # Get daily breakdown
        daily_pnl = self.pnl_calc.calculate_pnl_by_day(mode=mode, days=7)
        
        # Get best and worst positions
        best_worst = self.pnl_calc.get_best_and_worst_positions(mode=mode, n=3)
        
        mode_str = mode or "ALL MODES"
        week_str = f"{week_start.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
        
        lines = [
            "=" * 70,
            f"PORTFOLIO WEEKLY SUMMARY",
            f"Period: {week_str}",
            f"Mode: {mode_str}",
            "=" * 70,
            "",
            "WEEKLY PERFORMANCE:",
            f"  Realized P&L: ${weekly_realized:.2f}",
            f"  Current Unrealized P&L: ${summary['open_positions']['unrealized_pnl']:.2f}",
            f"  Total P&L: ${summary['total_pnl']:.2f}",
            "",
            "CURRENT PORTFOLIO:",
            f"  Open Positions: {summary['open_positions']['count']}",
            f"  Closed Positions (Total): {summary['closed_positions']['count']}",
            f"  Total Value: ${summary['open_positions']['total_value']:.2f}",
            "",
        ]
        
        # Add daily breakdown
        lines.append("DAILY ACTIVITY:")
        sorted_dates = sorted(daily_pnl.keys())[-7:]
        for date in sorted_dates:
            day_data = daily_pnl[date]
            lines.append(f"  {date}:")
            lines.append(f"    Opened: {day_data['positions_opened']}, Closed: {day_data['positions_closed']}")
            lines.append(f"    Realized P&L: ${day_data['realized_pnl']:.2f}")
            lines.append(f"    Net Invested: ${day_data['net_invested']:.2f}")
        lines.append("")
        
        # Add top performers
        if best_worst['best']:
            lines.append("TOP PERFORMERS:")
            for pos in best_worst['best']:
                pnl = pos.unrealized_pnl if pos.status == "open" else (pos.realized_pnl or 0)
                status = "OPEN" if pos.status == "open" else "CLOSED"
                lines.append(f"  [{status}] {pos.market_name[:50]}")
                lines.append(f"    P&L: ${pnl:.2f} ({pnl/pos.entry_amount*100:.1f}%)")
        
        # Add worst performers
        if best_worst['worst']:
            lines.append("")
            lines.append("WORST PERFORMERS:")
            for pos in best_worst['worst']:
                pnl = pos.unrealized_pnl if pos.status == "open" else (pos.realized_pnl or 0)
                status = "OPEN" if pos.status == "open" else "CLOSED"
                lines.append(f"  [{status}] {pos.market_name[:50]}")
                lines.append(f"    P&L: ${pnl:.2f} ({pnl/pos.entry_amount*100:.1f}%)")
        
        lines.append("")
        lines.append("=" * 70)
        
        report_text = "\n".join(lines)
        
        # Log report generation
        self.audit.log_action(
            action_type="weekly_summary_generated",
            action_data={'mode': mode or "ALL", 'week_start': week_start.isoformat()},
            result="success"
        )
        
        return report_text
    
    def export_positions_json(self, output_path: Path, mode: Optional[str] = None) -> None:
        """
        Export all positions to JSON file.
        
        Args:
            output_path: Path to output JSON file
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
        """
        positions = self.position_manager.get_all_positions(mode=mode)
        
        data = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'mode': mode or "ALL",
            'count': len(positions),
            'positions': [
                {
                    'position_id': pos.position_id,
                    'market_id': pos.market_id,
                    'market_name': pos.market_name,
                    'side': pos.side,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'quantity': pos.quantity,
                    'entry_amount': pos.entry_amount,
                    'current_value': pos.current_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_pct': pos.unrealized_pnl_pct,
                    'realized_pnl': pos.realized_pnl,
                    'status': pos.status,
                    'mode': pos.mode,
                    'opened_at': pos.opened_at,
                    'closed_at': pos.closed_at
                }
                for pos in positions
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.audit.log_action(
            action_type="positions_exported_json",
            action_data={'path': str(output_path), 'mode': mode or "ALL", 'count': len(positions)},
            result="success"
        )
    
    def export_positions_csv(self, output_path: Path, mode: Optional[str] = None) -> None:
        """
        Export all positions to CSV file.
        
        Args:
            output_path: Path to output CSV file
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
        """
        positions = self.position_manager.get_all_positions(mode=mode)
        
        if not positions:
            # Create empty CSV with headers
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'position_id', 'market_id', 'market_name', 'side',
                    'entry_price', 'current_price', 'quantity',
                    'entry_amount', 'current_value', 'unrealized_pnl',
                    'unrealized_pnl_pct', 'realized_pnl', 'status', 'mode',
                    'opened_at', 'closed_at'
                ])
            return
        
        fieldnames = [
            'position_id', 'market_id', 'market_name', 'side',
            'entry_price', 'current_price', 'quantity',
            'entry_amount', 'current_value', 'unrealized_pnl',
            'unrealized_pnl_pct', 'realized_pnl', 'status', 'mode',
            'opened_at', 'closed_at'
        ]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for pos in positions:
                writer.writerow({
                    'position_id': pos.position_id,
                    'market_id': pos.market_id,
                    'market_name': pos.market_name,
                    'side': pos.side,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'quantity': pos.quantity,
                    'entry_amount': pos.entry_amount,
                    'current_value': pos.current_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_pct': pos.unrealized_pnl_pct,
                    'realized_pnl': pos.realized_pnl or 0,
                    'status': pos.status,
                    'mode': pos.mode,
                    'opened_at': pos.opened_at,
                    'closed_at': pos.closed_at or ''
                })
        
        self.audit.log_action(
            action_type="positions_exported_csv",
            action_data={'path': str(output_path), 'mode': mode or "ALL", 'count': len(positions)},
            result="success"
        )
    
    def export_pnl_json(self, output_path: Path, mode: Optional[str] = None) -> None:
        """
        Export P&L report to JSON file.
        
        Args:
            output_path: Path to output JSON file
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
        """
        report = self.pnl_calc.get_pnl_report(mode=mode)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.audit.log_action(
            action_type="pnl_exported_json",
            action_data={'path': str(output_path), 'mode': mode or "ALL"},
            result="success"
        )
    
    def get_telegram_notification_text(self, mode: Optional[str] = None) -> str:
        """
        Generate concise text for Telegram notification.
        
        Args:
            mode: Filter by mode ("DRYRUN" or "LIVE", None for all)
            
        Returns:
            Short formatted text suitable for Telegram
        """
        summary = self.tracker.get_portfolio_summary(mode=mode)
        
        mode_str = mode or "ALL"
        emoji = "📊"
        
        lines = [
            f"{emoji} Portfolio Update ({mode_str})",
            "",
            f"💼 Open: {summary['open_positions']['count']} positions",
            f"💰 Value: ${summary['open_positions']['total_value']:.2f}",
            f"📈 Unrealized: ${summary['open_positions']['unrealized_pnl']:.2f} ({summary['open_positions']['unrealized_pnl_pct']:.1f}%)",
            f"💵 Realized: ${summary['closed_positions']['realized_pnl']:.2f}",
            f"📊 Total P&L: ${summary['total_pnl']:.2f}"
        ]
        
        # Add warning emoji if there's a problem
        health = self.tracker.get_portfolio_health_check(mode=mode)
        if health['warnings']:
            lines.append("")
            lines.append(f"⚠️ {len(health['warnings'])} warning(s)")
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Create report generator with test data
    generator = ReportGenerator()
    pm = generator.position_manager
    
    # Add test positions
    pos1 = pm.add_position(
        market_id="market_1",
        market_name="Will BTC hit $100k by EOY?",
        side="YES",
        entry_price=0.45,
        quantity=100.0,
        mode="DRYRUN"
    )
    pm.update_position_price(pos1.position_id, 0.55)
    
    pos2 = pm.add_position(
        market_id="market_2",
        market_name="Will S&P 500 reach 5000?",
        side="NO",
        entry_price=0.70,
        quantity=50.0,
        mode="DRYRUN"
    )
    pm.update_position_price(pos2.position_id, 0.65)
    pm.close_position(pos2.position_id, 0.60)
    
    # Generate reports
    print(generator.generate_daily_summary(mode="DRYRUN"))
    print("\n\n")
    print(generator.generate_weekly_summary(mode="DRYRUN"))
    print("\n\n")
    print("TELEGRAM NOTIFICATION:")
    print(generator.get_telegram_notification_text(mode="DRYRUN"))
    
    # Export to files
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "positions.json"
        csv_path = Path(tmpdir) / "positions.csv"
        pnl_path = Path(tmpdir) / "pnl_report.json"
        
        generator.export_positions_json(json_path, mode="DRYRUN")
        generator.export_positions_csv(csv_path, mode="DRYRUN")
        generator.export_pnl_json(pnl_path, mode="DRYRUN")
        
        print(f"\n\nExported files to: {tmpdir}")
