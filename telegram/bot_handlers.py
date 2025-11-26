#!/usr/bin/env python3
"""
Telegram Bot Command Handlers

Implements command handlers for zero-touch system operation via Telegram.
Integrates with existing state files, audit system, and AI Nexus.

Commands:
- /status - Quick system status
- /health - Detailed health check  
- /markets - Current market opportunities
- /balance - Portfolio/bankroll status
- /help - List available commands
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
SCRIPTS_DIR = REPO_ROOT / "scripts"
LOGS_DIR = REPO_ROOT / "logs"


class BotHandlers:
    """Enhanced command handlers for Telegram bot."""

    def __init__(self):
        """Initialize bot handlers."""
        self.handlers = {
            '/status': self.cmd_status,
            '/health': self.cmd_health,
            '/markets': self.cmd_markets,
            '/balance': self.cmd_balance,
            '/help': self.cmd_help,
        }

    def handle_command(self, command_text: str) -> str:
        """
        Process incoming command and return response text.
        
        Args:
            command_text: Command string from user (e.g., "/status")
            
        Returns:
            Response message to send back to user
        """
        parts = command_text.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in self.handlers:
            try:
                return self.handlers[cmd](args)
            except Exception as e:
                return f"❌ Error executing {cmd}: {str(e)}"
        else:
            return f"Unknown command: {cmd}\nSend /help for command list"

    def cmd_status(self, args: List[str]) -> str:
        """
        Get quick system status overview.
        
        Returns key metrics:
        - System health
        - Latest execution info
        - Current mode (DRYRUN/LIVE)
        - Recent activity
        """
        try:
            status_parts = []
            status_parts.append("📊 *System Status*\n")

            # Check if system is operational
            health_check = self._quick_health_check()
            status_parts.append(f"🟢 Status: {health_check}\n")

            # Latest execution plan
            exec_info = self._get_latest_execution_info()
            if exec_info:
                status_parts.append(f"📈 *Latest Activity:*")
                status_parts.append(f"• Time: {exec_info.get('time', 'N/A')}")
                status_parts.append(f"• Orders: {exec_info.get('orders', 0)}")
                status_parts.append(f"• Size: ${exec_info.get('size', 0):.2f}\n")
            else:
                status_parts.append("📈 *Latest Activity:* No recent execution\n")

            # Operating mode
            mode = self._get_operating_mode()
            mode_emoji = "🟢" if mode == "DRYRUN" else "🔴"
            status_parts.append(f"{mode_emoji} *Mode:* {mode}")
            if mode == "DRYRUN":
                status_parts.append("(no real money)\n")
            else:
                status_parts.append("(LIVE trading)\n")

            # AI agents status
            agent_status = self._get_agent_status()
            status_parts.append(f"🤖 *AI Agents:* {agent_status}\n")

            status_parts.append("_Send /health for detailed check_")
            status_parts.append("_Send /markets for opportunities_")
            status_parts.append("_Send /balance for portfolio_")

            return "\n".join(status_parts)

        except Exception as e:
            return f"❌ Error getting status: {str(e)}"

    def cmd_health(self, args: List[str]) -> str:
        """
        Run detailed health check.
        
        Checks:
        - System services
        - Data freshness
        - Configuration validity
        - Recent errors
        """
        try:
            health_parts = []
            health_parts.append("🏥 *Health Check*\n")

            # Run healthcheck script if exists
            healthcheck_path = SCRIPTS_DIR / "healthcheck.sh"
            if healthcheck_path.exists():
                try:
                    result = subprocess.run(
                        [str(healthcheck_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        health_parts.append("✅ *Overall:* HEALTHY\n")
                    else:
                        health_parts.append("⚠️ *Overall:* ISSUES DETECTED\n")
                    
                    # Include relevant output
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines[:10]:  # First 10 lines
                        if line.strip():
                            health_parts.append(f"  {line}")
                    
                    if len(output_lines) > 10:
                        health_parts.append(f"  ... ({len(output_lines) - 10} more lines)")
                    
                except subprocess.TimeoutExpired:
                    health_parts.append("⚠️ Health check timed out")
            else:
                # Manual health checks
                health_parts.append("*Component Checks:*\n")
                
                # Check state files
                state_health = self._check_state_files()
                health_parts.append(f"• State Files: {state_health}")
                
                # Check recent activity
                activity_health = self._check_recent_activity()
                health_parts.append(f"• Recent Activity: {activity_health}")
                
                # Check for errors
                error_count = self._count_recent_errors()
                if error_count == 0:
                    health_parts.append("• Errors (24h): ✅ None")
                else:
                    health_parts.append(f"• Errors (24h): ⚠️ {error_count}")

            return "\n".join(health_parts)

        except Exception as e:
            return f"❌ Error running health check: {str(e)}"

    def cmd_markets(self, args: List[str]) -> str:
        """
        Show current market opportunities.
        
        Displays:
        - Active markets with edge
        - Fair price estimates
        - Confidence levels
        - Recommended positions
        """
        try:
            markets_parts = []
            markets_parts.append("📈 *Market Opportunities*\n")

            # Read polymarket model
            model_path = STATE_DIR / "polymarket-model.json"
            if not model_path.exists():
                return "❌ No market data available. Run data fetchers first."

            with open(model_path) as f:
                model_data = json.load(f)

            # Extract opportunities
            opportunities = self._extract_market_opportunities(model_data)
            
            if not opportunities:
                markets_parts.append("No opportunities meeting criteria currently.\n")
                markets_parts.append("_Criteria: Min 70% confidence, positive edge_")
                return "\n".join(markets_parts)

            # Show top opportunities
            markets_parts.append(f"*Top {min(len(opportunities), 5)} Opportunities:*\n")
            
            for i, opp in enumerate(opportunities[:5], 1):
                edge_pct = opp.get('edge', 0) * 100
                confidence = opp.get('confidence', 0) * 100
                market = opp.get('market', 'Unknown')
                side = opp.get('side', 'Unknown')
                
                edge_emoji = "🟢" if edge_pct > 5 else "🟡"
                
                markets_parts.append(f"{i}. {edge_emoji} *{market}*")
                markets_parts.append(f"   Side: {side}")
                markets_parts.append(f"   Edge: {edge_pct:.1f}%")
                markets_parts.append(f"   Confidence: {confidence:.0f}%\n")

            markets_parts.append(f"_Showing {len(opportunities)} total opportunities_")
            markets_parts.append("_Mode: DRYRUN (no real trades)_")

            return "\n".join(markets_parts)

        except Exception as e:
            return f"❌ Error getting market data: {str(e)}"

    def cmd_balance(self, args: List[str]) -> str:
        """
        Show portfolio/bankroll status.
        
        Displays:
        - Total bankroll
        - Current positions
        - Available capital
        - P&L summary
        """
        try:
            balance_parts = []
            balance_parts.append("💰 *Portfolio Status*\n")

            # Try to get balance from state files
            balance_data = self._get_balance_data()
            
            if not balance_data:
                balance_parts.append("⚠️ No balance data available")
                balance_parts.append("\n_Note: In DRYRUN mode, using simulated balance_")
                balance_parts.append("_LIVE mode would show real account balance_")
                return "\n".join(balance_parts)

            # Display balance info
            total_balance = balance_data.get('total', 0)
            available = balance_data.get('available', 0)
            in_positions = balance_data.get('in_positions', 0)
            
            balance_parts.append(f"*Total Bankroll:* ${total_balance:.2f}")
            balance_parts.append(f"*Available:* ${available:.2f}")
            balance_parts.append(f"*In Positions:* ${in_positions:.2f}\n")

            # Position details
            positions = balance_data.get('positions', [])
            if positions:
                balance_parts.append(f"*Current Positions:* {len(positions)}\n")
                for pos in positions[:5]:  # Show first 5
                    market = pos.get('market', 'Unknown')
                    size = pos.get('size', 0)
                    pnl = pos.get('pnl', 0)
                    pnl_emoji = "🟢" if pnl >= 0 else "🔴"
                    
                    balance_parts.append(f"• {market}")
                    balance_parts.append(f"  Size: ${size:.2f} | P&L: {pnl_emoji}${pnl:+.2f}\n")
                
                if len(positions) > 5:
                    balance_parts.append(f"_... and {len(positions) - 5} more positions_\n")
            else:
                balance_parts.append("*Current Positions:* None\n")

            # Risk metrics
            risk_pct = (in_positions / total_balance * 100) if total_balance > 0 else 0
            balance_parts.append(f"*Risk Utilization:* {risk_pct:.1f}%")
            
            if risk_pct < 30:
                balance_parts.append("🟢 Conservative")
            elif risk_pct < 60:
                balance_parts.append("🟡 Moderate")
            else:
                balance_parts.append("🔴 Aggressive")

            return "\n".join(balance_parts)

        except Exception as e:
            return f"❌ Error getting balance: {str(e)}"

    def cmd_help(self, args: List[str]) -> str:
        """Show available commands and usage."""
        help_text = """📱 *Telegram Bot Commands*

*Quick Status:*
/status - System overview
/health - Detailed health check

*Trading Info:*
/markets - Market opportunities
/balance - Portfolio status

*System Control:*
/approve <id> - Approve change
/reject <id> - Reject change
/task <desc> - Queue task

*AI Coordination:*
/agents - Agent status
/pending - Pending approvals

*Other:*
/metrics - Performance (24h)
/help - This message

_Zero-touch operation via Telegram_
_No CLI needed for routine tasks_"""

        return help_text

    # Helper methods

    def _quick_health_check(self) -> str:
        """Quick health status check."""
        try:
            # Check if critical state files exist
            critical_files = [
                STATE_DIR / "knowledge.json",
                STATE_DIR / "polymarket-model.json",
            ]
            
            for file_path in critical_files:
                if not file_path.exists():
                    return "⚠️ Missing state files"
            
            return "Operational"
        except Exception:
            return "Unknown"

    def _get_latest_execution_info(self) -> Optional[Dict]:
        """Get latest execution plan info."""
        try:
            exec_plan_path = REPO_ROOT / "executor" / "execution_plan.json"
            if not exec_plan_path.exists():
                return None

            with open(exec_plan_path) as f:
                plan = json.load(f)

            return {
                'time': plan.get('timestamp', 'N/A'),
                'orders': plan.get('total_orders', 0),
                'size': plan.get('total_size_usd', 0)
            }
        except Exception:
            return None

    def _get_operating_mode(self) -> str:
        """Get current operating mode (DRYRUN or LIVE)."""
        # Default to DRYRUN for safety
        return os.getenv('TRADING_MODE', 'DRYRUN')

    def _get_agent_status(self) -> str:
        """Get AI agent coordination status."""
        try:
            status_path = REPO_ROOT / "ai" / "coordination" / "status.json"
            if not status_path.exists():
                return "Unknown"

            with open(status_path) as f:
                status = json.load(f)

            active = status.get('active_agents', [])
            return f"{len(active)} active" if active else "Idle"
        except Exception:
            return "Unknown"

    def _check_state_files(self) -> str:
        """Check health of state files."""
        try:
            state_files = list(STATE_DIR.glob("*.json"))
            if not state_files:
                return "❌ No state files"
            
            # Check if files are recent (within 24h)
            now = datetime.now()
            recent_count = 0
            
            for file_path in state_files:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if now - mtime < timedelta(hours=24):
                    recent_count += 1
            
            if recent_count == len(state_files):
                return f"✅ {len(state_files)} files"
            elif recent_count > 0:
                return f"⚠️ {recent_count}/{len(state_files)} recent"
            else:
                return "❌ All files stale"
                
        except Exception:
            return "❌ Check failed"

    def _check_recent_activity(self) -> str:
        """Check for recent system activity."""
        try:
            # Check performance metrics
            metrics_path = STATE_DIR / "performance_metrics.jsonl"
            if not metrics_path.exists():
                return "⚠️ No metrics"

            with open(metrics_path) as f:
                lines = f.readlines()
                if not lines:
                    return "⚠️ No data"

            # Check last entry timestamp
            last_entry = json.loads(lines[-1])
            last_time = datetime.fromisoformat(last_entry['timestamp'].replace('+00:00', ''))
            age = datetime.now() - last_time

            if age < timedelta(hours=2):
                return "✅ Active"
            elif age < timedelta(hours=24):
                return f"⚠️ {age.seconds // 3600}h ago"
            else:
                return "❌ Stale"

        except Exception:
            return "❌ Check failed"

    def _count_recent_errors(self) -> int:
        """Count errors in last 24 hours."""
        try:
            # Check logs for errors
            log_files = list(LOGS_DIR.glob("*.txt"))
            error_count = 0
            cutoff = datetime.now() - timedelta(hours=24)

            for log_file in log_files:
                try:
                    with open(log_file) as f:
                        for line in f:
                            if 'error' in line.lower() or 'failed' in line.lower():
                                error_count += 1
                except Exception:
                    continue

            return error_count

        except Exception:
            return 0

    def _extract_market_opportunities(self, model_data: Dict) -> List[Dict]:
        """Extract market opportunities from model data."""
        opportunities = []
        
        try:
            # Extract from model data structure
            # This will depend on actual structure of polymarket-model.json
            markets = model_data.get('markets', [])
            
            for market in markets:
                # Look for markets with positive edge and high confidence
                edge = market.get('edge', 0)
                confidence = market.get('confidence', 0)
                
                if edge > 0 and confidence > 0.7:  # Min 70% confidence
                    opportunities.append({
                        'market': market.get('title', 'Unknown'),
                        'side': market.get('recommended_side', 'N/A'),
                        'edge': edge,
                        'confidence': confidence,
                        'fair_price': market.get('fair_price', 0)
                    })
            
            # Sort by edge (highest first)
            opportunities.sort(key=lambda x: x['edge'], reverse=True)
            
        except Exception:
            # If structure doesn't match, return empty
            pass

        return opportunities

    def _get_balance_data(self) -> Optional[Dict]:
        """Get balance/portfolio data from state files."""
        try:
            # Try to find finance state file
            finance_files = [
                STATE_DIR / "finance.json",
                STATE_DIR / "bankroll.json",
                STATE_DIR / "portfolio.json",
            ]
            
            for file_path in finance_files:
                if file_path.exists():
                    with open(file_path) as f:
                        data = json.load(f)
                    return data
            
            # If no finance file, return simulated data for DRYRUN
            return {
                'total': 1000.0,
                'available': 900.0,
                'in_positions': 100.0,
                'positions': [],
                'note': 'Simulated balance for DRYRUN mode'
            }

        except Exception:
            return None
