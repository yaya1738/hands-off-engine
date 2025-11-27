#!/usr/bin/env python3
"""
Autonomous Trader: Continuous Trading Loop
===========================================

Runs continuously without human intervention:
- Fetches fresh market data every 15 minutes
- Runs decider to identify opportunities
- Executes trades via executor
- Logs results to logs/trading.jsonl
- Sends Telegram alerts on significant events (>$10 profit/loss)
- Self-recovers from errors
- Graceful shutdown handling

Usage:
    python3 scripts/autonomous_trader.py [--interval 900] [--bankroll 1000]

Health check:
    curl http://localhost:8899/health
"""

import argparse
import json
import os
import signal
import sys
import time
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.sync_polymarket_model import sync_polymarket_model
from decider.ho_decider import Decider
from executor.ho_executor_plan import Executor
from audit import get_audit_logger


@dataclass
class TradingCycleResult:
    """Result of a single trading cycle."""
    timestamp: str
    cycle_number: int
    success: bool
    error: Optional[str]
    markets_analyzed: int
    opportunities_found: int
    trades_executed: int
    trades_rejected: int
    total_amount: float
    duration_seconds: float
    mode: str


class TradingLogger:
    """Logger for trading results in JSONL format."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "trading.jsonl"
    
    def log(self, result: TradingCycleResult):
        """Append a trading cycle result to the log."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(asdict(result)) + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write trading log: {e}", file=sys.stderr)


class TelegramAlerter:
    """Send alerts via Telegram for significant events."""
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
    
    def send_alert(self, message: str, severity: str = "info"):
        """Send alert message via Telegram."""
        if not self.enabled:
            return
        
        try:
            import requests
            
            emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "🔴"}.get(severity, "📊")
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": f"{emoji} {message}",
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            print(f"[WARNING] Failed to send Telegram alert: {e}", file=sys.stderr)
    
    def alert_significant_event(self, result: TradingCycleResult):
        """Send alert if trading result is significant (>$10 movement)."""
        if result.total_amount >= 10.0:
            message = f"""**Trading Alert**
Cycle #{result.cycle_number}
• Trades executed: {result.trades_executed}
• Total amount: ${result.total_amount:.2f}
• Mode: {result.mode}"""
            self.send_alert(message, severity="info")
    
    def alert_error(self, error: str, cycle: int):
        """Send alert for trading errors."""
        message = f"""**Trading Error**
Cycle #{cycle}
Error: {error}

Auto-recovery in progress..."""
        self.send_alert(message, severity="error")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoint."""
    
    trader = None  # Set by AutonomousTrader
    
    def log_message(self, format, *args):
        # Suppress HTTP logging
        pass
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            health = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "running": self.trader.running if self.trader else False,
                "cycle_count": self.trader.cycle_count if self.trader else 0,
                "last_cycle": self.trader.last_cycle_time.isoformat() if self.trader and self.trader.last_cycle_time else None,
                "consecutive_errors": self.trader.consecutive_errors if self.trader else 0,
                "mode": "DRYRUN" if (self.trader and self.trader.dryrun) else "LIVE"
            }
            
            self.wfile.write(json.dumps(health).encode())
        else:
            self.send_response(404)
            self.end_headers()


class AutonomousTrader:
    """
    Autonomous trading loop that runs continuously.
    
    Features:
    - Runs every 15 minutes (configurable)
    - Fetches fresh market data
    - Runs decider to identify opportunities
    - Executes trades via executor (DRYRUN by default)
    - Logs results to trading.jsonl
    - Sends Telegram alerts on significant events
    - Self-recovers from errors
    - Graceful shutdown handling
    - Health check endpoint
    """
    
    # Maximum consecutive errors before alerting
    MAX_CONSECUTIVE_ERRORS = 3
    # Backoff multiplier for consecutive errors
    ERROR_BACKOFF_SECONDS = 60
    
    def __init__(
        self,
        interval: int = 900,  # 15 minutes
        bankroll: float = 1000.0,
        dryrun: bool = True,
        health_port: int = 8899
    ):
        """
        Initialize autonomous trader.
        
        Args:
            interval: Seconds between trading cycles (default: 900 = 15 min)
            bankroll: Total bankroll for position sizing
            dryrun: If True, no real trades executed (default: True)
            health_port: Port for health check HTTP server
        """
        self.interval = interval
        self.bankroll = bankroll
        self.dryrun = dryrun
        self.health_port = health_port
        
        self.repo_root = Path(__file__).parent.parent
        self.running = False
        self.cycle_count = 0
        self.consecutive_errors = 0
        self.last_cycle_time: Optional[datetime] = None
        
        # Setup components
        self.logger = TradingLogger(self.repo_root / "logs")
        self.alerter = TelegramAlerter()
        self.audit = get_audit_logger(component="autonomous_trader")
        
        # Signal handlers
        self._setup_signal_handlers()
        
        # Health check server
        self.health_server: Optional[HTTPServer] = None
        self.health_thread: Optional[threading.Thread] = None
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        print(f"\n[INFO] Received {sig_name}, shutting down gracefully...")
        self.running = False
    
    def _start_health_server(self):
        """Start HTTP health check server in background thread."""
        try:
            HealthCheckHandler.trader = self
            self.health_server = HTTPServer(("0.0.0.0", self.health_port), HealthCheckHandler)
            self.health_thread = threading.Thread(target=self.health_server.serve_forever, daemon=True)
            self.health_thread.start()
            print(f"[INFO] Health check server started on port {self.health_port}")
        except Exception as e:
            print(f"[WARNING] Could not start health server: {e}", file=sys.stderr)
    
    def _stop_health_server(self):
        """Stop HTTP health check server."""
        if self.health_server:
            self.health_server.shutdown()
            print("[INFO] Health check server stopped")
    
    def fetch_fresh_data(self) -> Dict:
        """
        Fetch fresh market data and generate alpha signals.
        
        Returns:
            Model dict with markets and signals
        """
        input_path = self.repo_root / "termux-hands-off" / "out" / "polymarket-compact.json"
        output_path = self.repo_root / "state" / "polymarket-model.json"
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input data not found: {input_path}")
        
        model = sync_polymarket_model(input_path, output_path)
        return model
    
    def run_decider(self, model: Dict) -> List:
        """
        Run decider to identify trading opportunities.
        
        Args:
            model: Model dict with markets
            
        Returns:
            List of PlannedAction objects
        """
        decider = Decider(bankroll=self.bankroll)
        
        # Transform model to signals format
        alpha_signals = []
        for market in model.get("markets", []):
            signal = {
                "market_id": market["market_id"],
                "market_name": market["question"],
                "edge": market["model_edge"],
                "current_odds": market["market_price"],
                "side": market["side"],
                "model_confidence": market["model_confidence"],
                "fair_price": market["fair_price"]
            }
            alpha_signals.append(signal)
        
        planned_actions = decider.plan_actions(alpha_signals)
        return planned_actions
    
    def execute_trades(self, planned_actions: List) -> tuple:
        """
        Execute trades via executor.
        
        Args:
            planned_actions: List of PlannedAction objects
            
        Returns:
            Tuple of (results, summary)
        """
        executor = Executor(dryrun=self.dryrun)
        results = executor.execute_actions(planned_actions)
        summary = executor.get_execution_summary(results)
        return results, summary
    
    def run_cycle(self) -> TradingCycleResult:
        """
        Run a single trading cycle.
        
        Returns:
            TradingCycleResult with cycle outcome
        """
        self.cycle_count += 1
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Fetch fresh data
            model = self.fetch_fresh_data()
            markets_analyzed = model.get("total_markets_analyzed", 0)
            
            # Step 2: Run decider
            planned_actions = self.run_decider(model)
            opportunities_found = len(planned_actions)
            
            # Step 3: Execute trades
            results, summary = self.execute_trades(planned_actions)
            
            # Calculate duration
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # Create result
            result = TradingCycleResult(
                timestamp=start_time.isoformat(),
                cycle_number=self.cycle_count,
                success=True,
                error=None,
                markets_analyzed=markets_analyzed,
                opportunities_found=opportunities_found,
                trades_executed=summary["successful"],
                trades_rejected=summary["rejected"],
                total_amount=summary["total_amount_executed"],
                duration_seconds=duration,
                mode=summary["mode"]
            )
            
            # Reset consecutive errors on success
            self.consecutive_errors = 0
            
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            self.consecutive_errors += 1
            
            return TradingCycleResult(
                timestamp=start_time.isoformat(),
                cycle_number=self.cycle_count,
                success=False,
                error=str(e),
                markets_analyzed=0,
                opportunities_found=0,
                trades_executed=0,
                trades_rejected=0,
                total_amount=0.0,
                duration_seconds=duration,
                mode="DRYRUN" if self.dryrun else "LIVE"
            )
    
    def run(self):
        """
        Main loop - runs continuously until shutdown signal.
        """
        print(f"\n{'='*70}")
        print("  AUTONOMOUS TRADER")
        print(f"{'='*70}")
        print(f"  Mode: {'DRYRUN (safe)' if self.dryrun else 'LIVE (real money!)'}")
        print(f"  Interval: {self.interval} seconds ({self.interval // 60} minutes)")
        print(f"  Bankroll: ${self.bankroll:.2f}")
        print(f"  Health check: http://localhost:{self.health_port}/health")
        print(f"{'='*70}\n")
        
        # Start health check server
        self._start_health_server()
        
        # Startup notification
        if self.alerter.enabled:
            self.alerter.send_alert(
                f"**Autonomous Trader Started**\n"
                f"Mode: {'DRYRUN' if self.dryrun else 'LIVE'}\n"
                f"Interval: {self.interval // 60} min",
                severity="success"
            )
        
        self.running = True
        
        try:
            while self.running:
                # Run trading cycle
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting cycle #{self.cycle_count + 1}")
                
                result = self.run_cycle()
                self.last_cycle_time = datetime.now(timezone.utc)
                
                # Log result
                self.logger.log(result)
                
                # Print summary
                if result.success:
                    print(f"  ✓ Cycle #{result.cycle_number} complete")
                    print(f"    Markets: {result.markets_analyzed}, Opportunities: {result.opportunities_found}")
                    print(f"    Executed: {result.trades_executed}, Rejected: {result.trades_rejected}")
                    print(f"    Total: ${result.total_amount:.2f} ({result.mode})")
                    print(f"    Duration: {result.duration_seconds:.2f}s")
                    
                    # Alert on significant events
                    self.alerter.alert_significant_event(result)
                else:
                    print(f"  ✗ Cycle #{result.cycle_number} failed: {result.error}")
                    
                    # Alert on consecutive errors
                    if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                        self.alerter.alert_error(result.error, result.cycle_number)
                
                # Audit log
                self.audit.log_action(
                    action_type="trading_cycle",
                    action_data=asdict(result),
                    result="success" if result.success else "error"
                )
                
                # Wait for next cycle (with error backoff if needed)
                if self.running:
                    wait_time = self.interval
                    if self.consecutive_errors > 0:
                        # Add backoff time for consecutive errors
                        wait_time += self.consecutive_errors * self.ERROR_BACKOFF_SECONDS
                        print(f"  [Backoff] Waiting extra {self.consecutive_errors * self.ERROR_BACKOFF_SECONDS}s due to errors")
                    
                    print(f"  Sleeping for {wait_time}s until next cycle...")
                    
                    # Sleep in small intervals to check for shutdown
                    for _ in range(wait_time):
                        if not self.running:
                            break
                        time.sleep(1)
        
        finally:
            # Cleanup
            self._stop_health_server()
            
            # Shutdown notification
            if self.alerter.enabled:
                self.alerter.send_alert(
                    f"**Autonomous Trader Stopped**\n"
                    f"Total cycles: {self.cycle_count}",
                    severity="warning"
                )
            
            print(f"\n[INFO] Autonomous Trader stopped after {self.cycle_count} cycles")


def main():
    """Entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Autonomous Trading Loop",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Seconds between trading cycles (default: 900 = 15 min)"
    )
    parser.add_argument(
        "--bankroll",
        type=float,
        default=1000.0,
        help="Total bankroll for position sizing"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in LIVE mode (real money!). Default is DRYRUN."
    )
    parser.add_argument(
        "--health-port",
        type=int,
        default=8899,
        help="Port for health check HTTP server"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one cycle only (useful for testing)"
    )
    
    args = parser.parse_args()
    
    # Safety check for live mode
    if args.live:
        print("\n⚠️  WARNING: You are about to run in LIVE mode with REAL MONEY!")
        print("   This will execute actual trades on Polymarket.")
        print("\n   Are you sure? Type 'YES' to continue: ", end="")
        
        confirmation = input().strip()
        if confirmation != "YES":
            print("✗ Aborted. Use --live only when you're ready for real trading.")
            return 1
    
    # Create and run trader
    trader = AutonomousTrader(
        interval=args.interval,
        bankroll=args.bankroll,
        dryrun=not args.live,
        health_port=args.health_port
    )
    
    if args.once:
        # Run single cycle for testing
        print("Running single cycle (--once mode)...")
        result = trader.run_cycle()
        trader.logger.log(result)
        print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
        if result.error:
            print(f"Error: {result.error}")
        return 0 if result.success else 1
    else:
        # Run continuous loop
        trader.run()
        return 0


if __name__ == "__main__":
    sys.exit(main())
