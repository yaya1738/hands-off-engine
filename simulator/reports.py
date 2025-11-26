"""
Reporting Module for Hands-Off Engine Simulator

Generates reports from backtest results:
- HTML/Markdown reports
- Performance charts (if matplotlib available)
- Trade-by-trade analysis
- Comparison tables
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .backtest import BacktestResult
from .metrics import PerformanceMetrics


class ReportGenerator:
    """
    Generates reports from backtest results.
    
    Supports multiple output formats and optional visualizations.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for reports (defaults to data/simulations/reports)
        """
        self.output_dir = output_dir or Path("data/simulations/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if matplotlib is available
        self.has_matplotlib = False
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            self.has_matplotlib = True
        except ImportError:
            pass
    
    def generate_markdown_report(
        self,
        result: BacktestResult,
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate a Markdown report from backtest results.
        
        Args:
            result: BacktestResult to report on
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{result.config.strategy_name}_{timestamp}.md"
        
        output_file = self.output_dir / filename
        
        # Generate report content
        summary = result.metrics.get_summary()
        
        lines = [
            f"# Backtest Report: {result.config.strategy_name}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Configuration",
            "",
            f"- **Strategy**: {result.config.strategy_name}",
            f"- **Start Date**: {result.config.start_date.strftime('%Y-%m-%d')}",
            f"- **End Date**: {result.config.end_date.strftime('%Y-%m-%d')}",
            f"- **Initial Capital**: ${result.config.initial_capital:,.2f}",
            f"- **Fee Rate**: {result.config.fee_rate * 100:.2f}%",
            f"- **Slippage Rate**: {result.config.slippage_rate * 100:.3f}%",
            "",
            "## Performance Summary",
            "",
            f"- **Final Portfolio Value**: ${result.final_portfolio_value:,.2f}",
            f"- **Total Return**: {result.total_return_pct:.2f}%",
            f"- **Total P&L**: ${summary.get('total_pnl', 0):.2f}",
            f"- **Number of Trades**: {result.num_trades}",
            "",
            "## Risk Metrics",
            "",
            f"- **Sharpe Ratio**: {summary.get('sharpe_ratio', 0):.3f}",
            f"- **Max Drawdown**: {summary.get('max_drawdown_pct', 0):.2f}% (${summary.get('max_drawdown_dollars', 0):,.2f})",
            "",
            "## Trading Metrics",
            "",
            f"- **Win Rate**: {summary.get('win_rate', 0):.2f}%",
            f"- **Profit Factor**: {summary.get('profit_factor', 0):.2f}",
            f"- **Average Win**: ${summary.get('average_win', 0):.2f}",
            f"- **Average Loss**: ${summary.get('average_loss', 0):.2f}",
            "",
        ]
        
        # Add success/error status
        if not result.success:
            lines.extend([
                "## Error",
                "",
                f"❌ Backtest failed: {result.error_message}",
                ""
            ])
        else:
            lines.extend([
                "## Status",
                "",
                "✅ Backtest completed successfully",
                ""
            ])
        
        # Write report
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        
        return output_file
    
    def generate_html_report(
        self,
        result: BacktestResult,
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate an HTML report from backtest results.
        
        Args:
            result: BacktestResult to report on
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{result.config.strategy_name}_{timestamp}.html"
        
        output_file = self.output_dir / filename
        
        # Generate report content
        summary = result.metrics.get_summary()
        
        status_badge = "✅ Success" if result.success else f"❌ Failed: {result.error_message}"
        status_class = "success" if result.success else "error"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Backtest Report: {result.config.strategy_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background-color: #f9f9f9;
            border-radius: 4px;
        }}
        .metric-label {{
            font-weight: 600;
            color: #666;
        }}
        .metric-value {{
            color: #333;
            font-family: monospace;
        }}
        .positive {{
            color: #4CAF50;
        }}
        .negative {{
            color: #f44336;
        }}
        .status {{
            padding: 10px 20px;
            border-radius: 4px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .status.success {{
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status.error {{
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Backtest Report: {result.config.strategy_name}</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="status {status_class}">
            {status_badge}
        </div>
        
        <h2>Configuration</h2>
        <div class="metric">
            <span class="metric-label">Strategy</span>
            <span class="metric-value">{result.config.strategy_name}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Period</span>
            <span class="metric-value">{result.config.start_date.strftime('%Y-%m-%d')} to {result.config.end_date.strftime('%Y-%m-%d')}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Initial Capital</span>
            <span class="metric-value">${result.config.initial_capital:,.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Fee Rate</span>
            <span class="metric-value">{result.config.fee_rate * 100:.2f}%</span>
        </div>
        
        <h2>Performance Summary</h2>
        <div class="metric">
            <span class="metric-label">Final Portfolio Value</span>
            <span class="metric-value">${result.final_portfolio_value:,.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Return</span>
            <span class="metric-value {'positive' if result.total_return_pct > 0 else 'negative'}">{result.total_return_pct:+.2f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total P&L</span>
            <span class="metric-value {'positive' if summary.get('total_pnl', 0) > 0 else 'negative'}">${summary.get('total_pnl', 0):+,.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Number of Trades</span>
            <span class="metric-value">{result.num_trades}</span>
        </div>
        
        <h2>Risk Metrics</h2>
        <div class="metric">
            <span class="metric-label">Sharpe Ratio</span>
            <span class="metric-value">{summary.get('sharpe_ratio', 0):.3f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Max Drawdown</span>
            <span class="metric-value negative">{summary.get('max_drawdown_pct', 0):.2f}% (${summary.get('max_drawdown_dollars', 0):,.2f})</span>
        </div>
        
        <h2>Trading Metrics</h2>
        <div class="metric">
            <span class="metric-label">Win Rate</span>
            <span class="metric-value">{summary.get('win_rate', 0):.2f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Profit Factor</span>
            <span class="metric-value">{summary.get('profit_factor', 0):.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Win</span>
            <span class="metric-value positive">${summary.get('average_win', 0):.2f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Loss</span>
            <span class="metric-value negative">${summary.get('average_loss', 0):.2f}</span>
        </div>
    </div>
</body>
</html>
"""
        
        # Write report
        with open(output_file, 'w') as f:
            f.write(html)
        
        return output_file
    
    def generate_comparison_table(
        self,
        results: List[BacktestResult],
        filename: Optional[str] = None,
        format: str = "markdown"
    ) -> Path:
        """
        Generate a comparison table for multiple backtest results.
        
        Args:
            results: List of BacktestResult objects
            filename: Output filename (auto-generated if None)
            format: Output format ("markdown" or "html")
            
        Returns:
            Path to generated report
        """
        if not results:
            raise ValueError("No results to compare")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "md" if format == "markdown" else "html"
            filename = f"comparison_{timestamp}.{ext}"
        
        output_file = self.output_dir / filename
        
        # Collect data from all results
        comparison_data = []
        for result in results:
            summary = result.metrics.get_summary()
            comparison_data.append({
                "strategy": result.config.strategy_name,
                "return": result.total_return_pct,
                "sharpe": summary.get('sharpe_ratio', 0),
                "max_dd": summary.get('max_drawdown_pct', 0),
                "win_rate": summary.get('win_rate', 0),
                "profit_factor": summary.get('profit_factor', 0),
                "num_trades": result.num_trades,
                "success": result.success
            })
        
        if format == "markdown":
            lines = [
                "# Strategy Comparison",
                "",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "| Strategy | Return % | Sharpe | Max DD % | Win Rate % | Profit Factor | Trades | Status |",
                "|----------|----------|--------|----------|------------|---------------|--------|--------|"
            ]
            
            for data in comparison_data:
                status = "✅" if data['success'] else "❌"
                lines.append(
                    f"| {data['strategy']} | "
                    f"{data['return']:+.2f} | "
                    f"{data['sharpe']:.3f} | "
                    f"{data['max_dd']:.2f} | "
                    f"{data['win_rate']:.2f} | "
                    f"{data['profit_factor']:.2f} | "
                    f"{data['num_trades']} | "
                    f"{status} |"
                )
            
            with open(output_file, 'w') as f:
                f.write('\n'.join(lines))
        
        else:  # HTML
            rows = ""
            for data in comparison_data:
                status = "✅" if data['success'] else "❌"
                return_class = "positive" if data['return'] > 0 else "negative"
                
                rows += f"""
                <tr>
                    <td>{data['strategy']}</td>
                    <td class="{return_class}">{data['return']:+.2f}%</td>
                    <td>{data['sharpe']:.3f}</td>
                    <td class="negative">{data['max_dd']:.2f}%</td>
                    <td>{data['win_rate']:.2f}%</td>
                    <td>{data['profit_factor']:.2f}</td>
                    <td>{data['num_trades']}</td>
                    <td>{status}</td>
                </tr>
                """
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Strategy Comparison</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Strategy Comparison</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Strategy</th>
                    <th>Return %</th>
                    <th>Sharpe</th>
                    <th>Max DD %</th>
                    <th>Win Rate %</th>
                    <th>Profit Factor</th>
                    <th>Trades</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
            
            with open(output_file, 'w') as f:
                f.write(html)
        
        return output_file
    
    def generate_trade_analysis(
        self,
        metrics: PerformanceMetrics,
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate trade-by-trade analysis report.
        
        Args:
            metrics: PerformanceMetrics with trade data
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trades_{timestamp}.md"
        
        output_file = self.output_dir / filename
        
        lines = [
            "# Trade-by-Trade Analysis",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Total Trades: {len(metrics.trades)}",
            "",
            "| # | Market | Side | Entry Time | Exit Time | Entry Price | Exit Price | P&L | Return % | Hold Hours |",
            "|---|--------|------|------------|-----------|-------------|------------|-----|----------|------------|"
        ]
        
        for i, trade in enumerate(metrics.trades, 1):
            lines.append(
                f"| {i} | "
                f"{trade.market_id} | "
                f"{trade.side} | "
                f"{trade.entry_time.strftime('%Y-%m-%d %H:%M')} | "
                f"{trade.exit_time.strftime('%Y-%m-%d %H:%M')} | "
                f"{trade.entry_price:.3f} | "
                f"{trade.exit_price:.3f} | "
                f"${trade.pnl:+.2f} | "
                f"{trade.return_pct:+.2f}% | "
                f"{trade.hold_duration_hours:.1f} |"
            )
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        
        return output_file


if __name__ == "__main__":
    # Example usage
    print("Report Generator Example\n" + "=" * 50)
    
    # This would normally use real backtest results
    print("Report generator is ready to use.")
    print("Usage:")
    print("  generator = ReportGenerator()")
    print("  generator.generate_markdown_report(result)")
    print("  generator.generate_html_report(result)")
    print("  generator.generate_comparison_table([result1, result2])")
