#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Unified Interface
==========================================

A single dashboard showing everything Yair needs to know:

SECTIONS:
1. IDENTITY      - Who am I serving
2. FINANCIAL     - Money state, runway, burn
3. TRADING       - Positions, P&L, signals
4. GOALS         - Active goals, progress
5. REALITY       - Current score, best future
6. ACTIONS       - What to do NOW
7. SYSTEM        - Health, daemons, bridges

OUTPUT MODES:
- Terminal (rich formatted)
- Telegram (markdown)
- JSON (API)
- HTML (web dashboard)

Serving: Yair Siegel
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


# =============================================================================
# DATA AGGREGATOR
# =============================================================================

class YairDataAggregator:
    """Aggregate data from all sources for Yair's UI."""

    def __init__(self):
        self.data = {}

    def load_all(self) -> Dict:
        """Load all data sources."""
        self.data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "identity": self._load_identity(),
            "financial": self._load_financial(),
            "wallet": self._load_wallet(),
            "trading": self._load_trading(),
            "golden": self._load_golden(),
            "goals": self._load_goals(),
            "reality": self._load_reality(),
            "actions": self._load_actions(),
            "system": self._load_system(),
        }
        return self.data

    def _load_identity(self) -> Dict:
        """Load Yair's identity."""
        try:
            kernel_path = STATE_DIR / "yair_context_kernel.json"
            if kernel_path.exists():
                with open(kernel_path) as f:
                    kernel = json.load(f)
                identity = kernel.get("identity", {})
                directive = kernel.get("directive", {})
                return {
                    "name": identity.get("name", "Yair Siegel"),
                    "aliases": identity.get("aliases", []),
                    "role": identity.get("role", "master"),
                    "directive": directive.get("primary", "")[:100],
                    "philosophy": directive.get("philosophy", [])[:3],
                }
        except:
            pass
        return {"name": "Yair Siegel", "role": "master"}

    def _load_financial(self) -> Dict:
        """Load financial state - INTEGRAFIX: Wire ALL wealth sources."""
        financial = {
            "liquid_usd": 0,
            "deployable": 0,
            "runway_months": 0,
            "monthly_burn": 0,
            "polymarket_balance": 0,
            "robinhood_balance": 0,
            "paypal_balance": 0,
            "credit_available": 0,
            "credit_debt": 0,
            "total_accessible": 0,
            "net_worth": 0,
            "trading_pnl": 0,
            "api_credits": 0,
            "infra_value": 0,
            "status": "unknown",
            "accounts": [],
            "assets": [],
        }

        try:
            # 1. From finance hub - cash accounts
            finance_path = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
            if finance_path.exists():
                with open(finance_path) as f:
                    hub = json.load(f)

                accounts = hub.get("accounts", {})

                # Polymarket
                pm = accounts.get("polymarket", {})
                financial["polymarket_balance"] = pm.get("balance_usdc", 0)
                if financial["polymarket_balance"] > 0:
                    financial["accounts"].append({"name": "Polymarket", "balance": financial["polymarket_balance"], "type": "cash"})

                # Robinhood
                rh = accounts.get("robinhood", {})
                financial["robinhood_balance"] = rh.get("balance_usd", 0)
                if financial["robinhood_balance"] > 0:
                    financial["accounts"].append({"name": "Robinhood", "balance": financial["robinhood_balance"], "type": "cash"})

                # PayPal Business
                pp = accounts.get("paypal_business", {})
                financial["paypal_balance"] = pp.get("balance_usd", 0)
                if financial["paypal_balance"] > 0:
                    financial["accounts"].append({"name": "PayPal", "balance": financial["paypal_balance"], "type": "cash"})

                # Credit
                credit = hub.get("credit", {})
                financial["credit_available"] = credit.get("total_available", 0)
                financial["credit_debt"] = credit.get("total_balance", 0)

                # Monthly burn
                burn = hub.get("monthly_burn", {})
                financial["monthly_burn"] = burn.get("total_usd", 0)

            # 2. Trading P&L from HFT ground truth
            hft_log = PROJECT_ROOT / "logs" / "hft_economics.jsonl"
            if hft_log.exists():
                pnl = 0.0
                with open(hft_log) as f:
                    for line in f:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "trade_close":
                                pnl += d.get("cost", 0)
                        except:
                            pass
                financial["trading_pnl"] = pnl
                if pnl != 0:
                    financial["assets"].append({"name": "Trading P&L", "value": pnl, "type": "earned"})

            # 3. API Credits from credit_optimizer
            credit_opt = STATE_DIR / "credit_optimizer.json"
            if credit_opt.exists():
                with open(credit_opt) as f:
                    co = json.load(f)
                balances = co.get("balances", {})
                total_credits = 0
                for provider, data in balances.items():
                    remaining = data.get("remaining_credits", 0)
                    # INTEGRAFIX: Skip infinity values (free tiers) for net worth calculation
                    if isinstance(remaining, (int, float)) and remaining > 0 and remaining < 1000000:
                        total_credits += remaining
                        financial["assets"].append({"name": f"{provider.title()} Credits", "value": remaining, "type": "credits"})
                    elif data.get("note") == "Free tier - unlimited usage":
                        # Show free tier providers but don't add to total
                        financial["assets"].append({"name": f"{provider.title()} (Free)", "value": 0, "type": "free"})
                financial["api_credits"] = total_credits

            # 4. Infrastructure value from mega_state
            mega = STATE_DIR / "mega_state.json"
            if mega.exists():
                with open(mega) as f:
                    ms = json.load(f)
                # Estimate infra value: $10/vCPU/month, $5/GB RAM
                vcpus = ms.get("total_vcpus", 0)
                ram = ms.get("total_ram_gb", 0)
                infra_monthly = vcpus * 10 + ram * 5
                financial["infra_value"] = infra_monthly
                if infra_monthly > 0:
                    financial["assets"].append({"name": "Infrastructure", "value": infra_monthly, "type": "compute"})

            # Calculate totals
            financial["liquid_usd"] = (
                financial["polymarket_balance"] +
                financial["robinhood_balance"] +
                financial["paypal_balance"]
            )
            financial["total_accessible"] = financial["liquid_usd"] + financial["credit_available"]
            financial["net_worth"] = (
                financial["liquid_usd"] +
                financial["trading_pnl"] +
                financial["api_credits"] -
                financial["credit_debt"]
            )
            financial["deployable"] = financial["total_accessible"]

            # Runway
            if financial["monthly_burn"] > 0:
                financial["runway_months"] = financial["total_accessible"] / financial["monthly_burn"]

            # Status based on runway
            if financial["runway_months"] < 1:
                financial["status"] = "CRITICAL"
            elif financial["runway_months"] < 3:
                financial["status"] = "WARNING"
            else:
                financial["status"] = "OK"

        except:
            pass

        return financial

    def _load_wallet(self) -> Dict:
        """Load actual wallet state - INTEGRAFIX: Show ALL wallets."""
        wallet = {
            "address": "Not configured",
            "balance": 0,
            "positions": 0,
            "unrealized_pnl": 0,
            "mode": "UNKNOWN",
            "total_wallets": 0,
            "funded_wallets": 0,
            "scale_wallets": [],
        }
        try:
            # Get main wallet from finance hub
            finance_path = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
            if finance_path.exists():
                with open(finance_path) as f:
                    hub = json.load(f)
                pm = hub.get("accounts", {}).get("polymarket", {})
                wallet["address"] = pm.get("wallet_address", "Not set")
                wallet["balance"] = pm.get("balance_usdc", 0)

            # Get trading mode from executor state
            exec_state = STATE_DIR / "trade_executor_state.json"
            if exec_state.exists():
                with open(exec_state) as f:
                    es = json.load(f)
                wallet["mode"] = es.get("mode", "UNKNOWN")

            # Get positions from polymarket_live_state
            pm_state = STATE_DIR / "polymarket_live_state.json"
            if pm_state.exists():
                with open(pm_state) as f:
                    pms = json.load(f)
                positions = pms.get("positions", [])
                wallet["positions"] = len(positions)
                wallet["unrealized_pnl"] = sum(p.get("unrealized_pnl", 0) for p in positions if isinstance(p, dict))

            # Get ALL wallets from registry
            registry_path = STATE_DIR / "wallets" / "registry.json"
            if registry_path.exists():
                with open(registry_path) as f:
                    registry = json.load(f)
                wallets = registry.get("wallets", {})
                wallet["total_wallets"] = len(wallets)
                wallet["funded_wallets"] = 1  # Only main wallet is funded
                # Get some scale wallet info
                for addr, data in list(wallets.items())[:5]:
                    wallet["scale_wallets"].append({
                        "alias": data.get("alias", "unknown"),
                        "address": addr[:10] + "...",
                        "status": data.get("status", "unknown"),
                    })

        except:
            pass
        return wallet

    def _load_trading(self) -> Dict:
        """INTEGRAFIX: Load trading state with TRUTH - distinguish REAL vs SIMULATED."""
        trading = {
            "mode": "DRYRUN",
            "real_trades": 0,
            "simulated_trades": 0,
            "resolved_trades": 0,  # Markets that actually settled
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "open_positions": 0,
            "signals_pending": 0,
            "opportunities": [],
            "safeguards": {},
        }

        try:
            # INTEGRAFIX: Get mode from trading_mode.json (single source of truth)
            mode_file = STATE_DIR / "trading_mode.json"
            if mode_file.exists():
                with open(mode_file) as f:
                    mode_data = json.load(f)
                trading["mode"] = "LIVE" if mode_data.get("live_trading_enabled") else "DRYRUN"
                trading["safeguards"] = mode_data.get("safeguards", {})

            # INTEGRAFIX: Get REAL trades from polymarket_live_state.json (ground truth)
            live_state = STATE_DIR / "polymarket_live_state.json"
            if live_state.exists():
                with open(live_state) as f:
                    live = json.load(f)
                trading["real_trades"] = live.get("total_trades", 0)
                trading["total_pnl"] = live.get("total_pnl", 0)
                trading["open_positions"] = len(live.get("positions", []))

            # INTEGRAFIX: Get SIMULATED trades from hft_economics.jsonl (tokens=0 means simulated)
            hft_log = PROJECT_ROOT / "logs" / "hft_economics.jsonl"
            if hft_log.exists():
                wins = 0
                simulated = 0
                pnl = 0.0
                with open(hft_log) as f:
                    for line in f:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "trade_close":
                                if d.get("tokens", 0) == 0:  # tokens=0 means simulated
                                    simulated += 1
                                cost = d.get("cost", 0)
                                pnl += cost
                                if cost > 0:
                                    wins += 1
                        except:
                            pass
                trading["simulated_trades"] = simulated
                trading["total_trades"] = trading["real_trades"] + simulated
                # Only use live P&L if we have real trades
                if trading["real_trades"] == 0:
                    trading["total_pnl"] = 0.0  # No real P&L from simulated trades

            # INTEGRAFIX: Get ACTUAL resolved trades from outcome_tracker (markets that settled)
            outcome_tracker = STATE_DIR / "outcome_tracker.json"
            if outcome_tracker.exists():
                with open(outcome_tracker) as f:
                    ot = json.load(f)
                trading["resolved_trades"] = ot.get("total_resolved", 0)
                trading["win_rate"] = ot.get("win_rate", 0)
            else:
                trading["resolved_trades"] = 0
                trading["win_rate"] = 0

            # From positions
            positions_path = STATE_DIR / "positions.json"
            if positions_path.exists():
                with open(positions_path) as f:
                    positions = json.load(f)
                trading["open_positions"] = len(positions.get("positions", {}))

            # Get opportunities from wisdom engine
            try:
                from autonomous.yair_wisdom_engine import YairWisdomEngine
                wisdom = YairWisdomEngine()
                arbs = wisdom.scan_merge_arbitrage()
                for arb in arbs[:2]:
                    trading["opportunities"].append({
                        "type": "merge_arb",
                        "market": arb["market"][:30],
                        "profit": f"${arb['profit_per_pair']:.3f}",
                    })
            except:
                pass

        except:
            pass

        return trading

    def _load_golden(self) -> Dict:
        """Load golden state - INTEGRAFIX: Wire Yair to Golden Path."""
        golden = {
            "tier": 0,
            "tier_name": "Unknown",
            "win_rate": 0,
            "total_trades": 0,
            "tier_trades": 0,
            "required_trades": 10,
            "required_wr": 0.52,
            "max_exposure": 200,
            "projection": 0,
            "target": 5000000,
            "gap": 5000000,
            "path": [],
        }
        try:
            from integrafix.golden_state import GoldenState
            gs = GoldenState.load()
            tier_cfg = gs.get_tier_config()
            golden["tier"] = gs.current_tier
            golden["tier_name"] = tier_cfg.name
            golden["win_rate"] = gs.win_rate
            golden["total_trades"] = gs.total_trades
            golden["tier_trades"] = gs.tier_trades
            golden["required_trades"] = tier_cfg.required_trades
            golden["required_wr"] = tier_cfg.required_win_rate
            golden["max_exposure"] = tier_cfg.max_exposure
            golden["projection"] = gs.monthly_projection()
            golden["gap"] = 5000000 - golden["projection"]
            golden["wr_gap"] = max(0, tier_cfg.required_win_rate - gs.win_rate)
            golden["path"] = [
                {"tier": 0, "name": "Validation", "exposure": 200},
                {"tier": 1, "name": "Foundation", "exposure": 500},
                {"tier": 2, "name": "Growth", "exposure": 5000},
                {"tier": 3, "name": "Acceleration", "exposure": 50000},
                {"tier": 4, "name": "Scale", "exposure": 200000},
                {"tier": 5, "name": "Golden", "exposure": 500000},
            ]
        except:
            pass
        return golden

    def _load_goals(self) -> Dict:
        """Load goals state."""
        goals = {
            "total": 0,
            "active": 0,
            "achieved": 0,
            "top_goals": [],
            "calibration": 0.5,
        }

        try:
            goals_path = STATE_DIR / "tracked_goals.json"
            if goals_path.exists():
                with open(goals_path) as f:
                    data = json.load(f)
                goal_list = data.get("goals", [])
                goals["total"] = len(goal_list)
                goals["active"] = len([g for g in goal_list if g.get("status") == "active"])
                goals["achieved"] = len([g for g in goal_list if g.get("status") == "achieved"])

                # Top 3 by priority
                active_goals = [g for g in goal_list if g.get("status") == "active"]
                sorted_goals = sorted(active_goals, key=lambda g: g.get("priority", 0), reverse=True)
                for g in sorted_goals[:3]:
                    goals["top_goals"].append({
                        "name": g["name"],
                        "progress": g.get("progress", 0),
                        "target": g.get("target", {}).get("value"),
                    })

            # Calibration
            bridge_path = STATE_DIR / "goals_effects_bridge.json"
            if bridge_path.exists():
                with open(bridge_path) as f:
                    bridge = json.load(f)
                goals["calibration"] = bridge.get("calibration_score", 0.5)

        except:
            pass

        return goals

    def _load_reality(self) -> Dict:
        """Load reality state."""
        reality = {
            "score": 0.5,
            "urgency": "NORMAL",
            "best_future": "",
            "expected_outcome": 0,
            "immediate_action": "",
        }

        try:
            bridge_path = STATE_DIR / "reality_bridge.json"
            if bridge_path.exists():
                with open(bridge_path) as f:
                    bridge = json.load(f)

                snapshot = bridge.get("last_snapshot", {})
                # Calculate score from snapshot
                fin = snapshot.get("financial", {})
                runway = fin.get("runway_months", 0)

                if runway < 1:
                    reality["score"] = runway * 0.5
                    reality["urgency"] = "CRITICAL"
                elif runway < 3:
                    reality["score"] = 0.5 + (runway - 1) * 0.15
                    reality["urgency"] = "HIGH"
                else:
                    reality["score"] = min(1.0, 0.8 + runway * 0.02)
                    reality["urgency"] = "NORMAL"

            # Get recommendation
            try:
                from integrafix.reality_bridge import get_reality_bridge
                rb = get_reality_bridge()
                rec = rb.recommend_action()
                reality["best_future"] = rec.get("best_future", {}).get("name", "")
                reality["expected_outcome"] = rec.get("best_future", {}).get("expected_outcome", 0)
                reality["immediate_action"] = rec.get("immediate_action", "")
            except:
                pass

        except:
            pass

        return reality

    def _load_actions(self) -> Dict:
        """Load recommended actions."""
        actions = {
            "immediate": [],
            "today": [],
            "this_week": [],
        }

        # Immediate actions based on urgency
        try:
            # From reality bridge
            from integrafix.reality_bridge import get_reality_bridge
            rb = get_reality_bridge()
            rec = rb.recommend_action()

            if rec.get("immediate_action"):
                actions["immediate"].append(rec["immediate_action"])

            for action in rec.get("all_actions", [])[:3]:
                if action not in actions["immediate"]:
                    actions["today"].append(action)

        except:
            pass

        # From trading opportunities
        try:
            from autonomous.yair_wisdom_engine import YairWisdomEngine
            wisdom = YairWisdomEngine()
            arbs = wisdom.scan_merge_arbitrage()
            if arbs:
                actions["immediate"].append(f"Merge Arb: {arbs[0]['market'][:25]}")
        except:
            pass

        return actions

    def _load_system(self) -> Dict:
        """Load system state."""
        system = {
            "daemons": {"running": 0, "total": 3},
            "bridges": 0,
            "cron_jobs": 0,
            "health_score": 0,
            "issues": [],
        }

        try:
            import subprocess

            # Daemons
            daemons = ["hardware_brain", "self_healer", "backend_loop"]
            running = 0
            for d in daemons:
                result = subprocess.run(["pgrep", "-f", d], capture_output=True)
                if result.returncode == 0:
                    running += 1
                else:
                    system["issues"].append(f"{d} not running")

            system["daemons"]["running"] = running
            system["health_score"] = running / len(daemons)

            # Bridges
            bridges = list((PROJECT_ROOT / "integrafix").glob("*.py"))
            system["bridges"] = len([b for b in bridges if not b.stem.startswith("_")])

            # Cron
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith("#")]
                system["cron_jobs"] = len(lines)

        except:
            pass

        return system


# =============================================================================
# UI RENDERERS
# =============================================================================

class TerminalUI:
    """Render UI for terminal."""

    def __init__(self, data: Dict):
        self.data = data

    def render(self) -> str:
        """Render full terminal UI."""
        lines = []

        # Header
        identity = self.data.get("identity", {})
        lines.append("=" * 70)
        lines.append(f"  YAIR SIEGEL DASHBOARD")
        lines.append(f"  {self.data.get('timestamp', '')}")
        lines.append("=" * 70)

        # Financial Section - INTEGRAFIX: Show ALL wealth
        fin = self.data.get("financial", {})
        status_icon = {"CRITICAL": "🔴", "WARNING": "🟡", "OK": "🟢"}.get(fin.get("status"), "⚪")
        lines.append(f"\n{status_icon} FINANCIAL [{fin.get('status', 'UNKNOWN')}]")
        lines.append(f"  ├─ Total Accessible: ${fin.get('total_accessible', 0):,.2f}")
        lines.append(f"  ├─ Liquid Cash:      ${fin.get('liquid_usd', 0):,.2f}")
        lines.append(f"  ├─ Credit Available: ${fin.get('credit_available', 0):,.0f}")
        lines.append(f"  ├─ Credit Debt:      ${fin.get('credit_debt', 0):,.0f}")
        lines.append(f"  ├─ Net Worth:        ${fin.get('net_worth', 0):+,.0f}")
        lines.append(f"  ├─ Burn:             ${fin.get('monthly_burn', 0):,.0f}/mo")
        lines.append(f"  └─ Runway:           {fin.get('runway_months', 0):.1f} months")
        # Show all accounts
        if fin.get("accounts"):
            lines.append("  CASH ACCOUNTS:")
            for acc in fin["accounts"]:
                lines.append(f"    💵 {acc['name']}: ${acc['balance']:,.2f}")
        # Show assets
        if fin.get("assets"):
            lines.append("  OTHER ASSETS:")
            for asset in fin["assets"]:
                lines.append(f"    📦 {asset['name']}: ${asset['value']:,.2f}")

        # Wallet Section - INTEGRAFIX: Show ALL wallets
        wallet = self.data.get("wallet", {})
        mode = wallet.get("mode", "UNKNOWN")
        mode_icon = "🟢" if mode == "LIVE" else "🟡" if mode == "DRYRUN" else "🔴"
        lines.append(f"\n{mode_icon} WALLETS [{mode}]")
        lines.append(f"  ├─ Total Wallets: {wallet.get('total_wallets', 0)}")
        lines.append(f"  ├─ Funded: {wallet.get('funded_wallets', 0)}")
        lines.append(f"  ├─ Main: {wallet.get('address', 'Not set')[:20]}...")
        lines.append(f"  ├─ Balance: ${wallet.get('balance', 0):.2f} USDC")
        lines.append(f"  ├─ Positions: {wallet.get('positions', 0)}")
        lines.append(f"  └─ Unrealized: ${wallet.get('unrealized_pnl', 0):+.2f}")
        if wallet.get("total_wallets", 0) > 1:
            unfunded = wallet.get("total_wallets", 0) - wallet.get("funded_wallets", 0)
            lines.append(f"  ⚠️  {unfunded} wallets unfunded (ready for scaling)")

        # Trading Section - INTEGRAFIX: Show TRUE state (REAL vs SIMULATED)
        trading = self.data.get("trading", {})
        mode = trading.get("mode", "DRYRUN")
        mode_icon = "🟢" if mode == "LIVE" else "🟡"
        real_trades = trading.get("real_trades", 0)
        simulated_trades = trading.get("simulated_trades", 0)
        resolved_trades = trading.get("resolved_trades", 0)
        lines.append(f"\n{mode_icon} TRADING [{mode}]")
        lines.append(f"  ├─ REAL Trades:    {real_trades}")
        lines.append(f"  ├─ Simulated:      {simulated_trades}")
        lines.append(f"  ├─ Resolved:       {resolved_trades} (markets settled)")
        lines.append(f"  ├─ Real P&L:       ${trading.get('total_pnl', 0):+.2f}")
        lines.append(f"  └─ Open Positions: {trading.get('open_positions', 0)}")
        # Show safeguards if in LIVE mode
        safeguards = trading.get("safeguards", {})
        if mode == "LIVE" and safeguards:
            lines.append("  SAFEGUARDS:")
            lines.append(f"    Max/Trade: ${safeguards.get('max_per_trade', 0):.0f}")
            lines.append(f"    Max Daily Loss: ${safeguards.get('max_daily_loss', 0):.0f}")
            lines.append(f"    Min Edge: {safeguards.get('min_edge_required', 0)*100:.0f}%")
        if real_trades == 0 and mode == "LIVE":
            lines.append("  ⚠️  LIVE mode enabled but 0 real trades yet")
        if simulated_trades > 0 and resolved_trades == 0:
            lines.append("  ⚠️  No markets resolved yet - win rate unknown")

        if trading.get("opportunities"):
            lines.append("  OPPORTUNITIES:")
            for opp in trading["opportunities"]:
                lines.append(f"    • [{opp['type']}] {opp['market']} ({opp['profit']})")

        # Golden State Section - INTEGRAFIX: Wire Yair to Golden Path
        golden = self.data.get("golden", {})
        tier = golden.get("tier", 0)
        wr_gap = golden.get("wr_gap", 0)
        gold_icon = "🏆" if tier >= 5 else "⭐" if tier >= 3 else "🎯"
        lines.append(f"\n{gold_icon} GOLDEN PATH [Tier {tier}: {golden.get('tier_name', 'Unknown')}]")
        lines.append(f"  ├─ Max Exposure: ${golden.get('max_exposure', 0):,}")
        lines.append(f"  ├─ Projection:   ${golden.get('projection', 0):,.0f}/month")
        lines.append(f"  ├─ Target:       $5,000,000/month")
        lines.append(f"  └─ Gap:          ${golden.get('gap', 0):,.0f}")
        # Show tier path
        lines.append("  PATH:")
        for p in golden.get("path", []):
            if p["tier"] < tier:
                lines.append(f"    ✅ Tier {p['tier']}: {p['name']}")
            elif p["tier"] == tier:
                lines.append(f"    → Tier {p['tier']}: {p['name']} ← YOU")
            else:
                lines.append(f"    ○ Tier {p['tier']}: {p['name']}")
        if wr_gap > 0:
            lines.append(f"  ⚠️  Need +{wr_gap*100:.1f}% WR to advance")

        # Goals Section
        goals = self.data.get("goals", {})
        lines.append(f"\n📎 GOALS")
        lines.append(f"  ├─ Active:   {goals.get('active', 0)}/{goals.get('total', 0)}")
        lines.append(f"  ├─ Achieved: {goals.get('achieved', 0)}")
        lines.append(f"  └─ Calibration: {goals.get('calibration', 0.5):.0%}")

        if goals.get("top_goals"):
            lines.append("  TOP GOALS:")
            for g in goals["top_goals"]:
                progress = g.get("progress", 0)
                bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))
                lines.append(f"    [{bar}] {g['name']}")

        # Reality Section
        reality = self.data.get("reality", {})
        urgency = reality.get("urgency", "NORMAL")
        urg_icon = {"CRITICAL": "🔴", "HIGH": "🟡", "NORMAL": "🟢"}.get(urgency, "⚪")
        lines.append(f"\n{urg_icon} REALITY [{urgency}]")
        lines.append(f"  ├─ Score:    {reality.get('score', 0.5):.0%}")
        lines.append(f"  ├─ Best Path: {reality.get('best_future', 'Unknown')}")
        lines.append(f"  └─ Expected: ${reality.get('expected_outcome', 0):+,.0f}")

        # Actions Section
        actions = self.data.get("actions", {})
        lines.append(f"\n⚡ ACTIONS")
        if actions.get("immediate"):
            lines.append("  IMMEDIATE:")
            for a in actions["immediate"][:3]:
                lines.append(f"    → {a}")
        if actions.get("today"):
            lines.append("  TODAY:")
            for a in actions["today"][:3]:
                lines.append(f"    • {a}")

        # System Section
        system = self.data.get("system", {})
        health = system.get("health_score", 0)
        health_icon = "🟢" if health >= 0.9 else "🟡" if health >= 0.5 else "🔴"
        lines.append(f"\n{health_icon} SYSTEM")
        lines.append(f"  ├─ Daemons:  {system.get('daemons', {}).get('running', 0)}/{system.get('daemons', {}).get('total', 3)}")
        lines.append(f"  ├─ Bridges:  {system.get('bridges', 0)}")
        lines.append(f"  └─ Cron:     {system.get('cron_jobs', 0)} jobs")

        if system.get("issues"):
            lines.append("  ISSUES:")
            for issue in system["issues"][:3]:
                lines.append(f"    ⚠ {issue}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)


class TelegramUI:
    """Render UI for Telegram."""

    def __init__(self, data: Dict):
        self.data = data

    def render_summary(self) -> str:
        """Render compact summary for Telegram."""
        fin = self.data.get("financial", {})
        trading = self.data.get("trading", {})
        reality = self.data.get("reality", {})
        system = self.data.get("system", {})

        status = fin.get("status", "UNKNOWN")
        status_emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "OK": "🟢"}.get(status, "⚪")

        lines = [
            f"*YAIR DASHBOARD* {status_emoji}",
            "",
            f"💰 *Financial*",
            f"  Runway: {fin.get('runway_months', 0):.1f}mo | Deploy: ${fin.get('deployable', 0)}",
            "",
            f"📈 *Trading*",
            f"  Win: {trading.get('win_rate', 0):.0%} | P&L: ${trading.get('total_pnl', 0):+.0f}",
            "",
            f"🎯 *Reality*",
            f"  Score: {reality.get('score', 0.5):.0%} | {reality.get('urgency', 'NORMAL')}",
            f"  Best: {reality.get('best_future', 'Unknown')[:20]}",
            "",
            f"⚙️ *System*",
            f"  Daemons: {system.get('daemons', {}).get('running', 0)}/3 | Bridges: {system.get('bridges', 0)}",
        ]

        actions = self.data.get("actions", {})
        if actions.get("immediate"):
            lines.append("")
            lines.append("⚡ *DO NOW*")
            lines.append(f"  → {actions['immediate'][0][:40]}")

        return "\n".join(lines)

    def render_full(self) -> str:
        """Render full report for Telegram."""
        return self.render_summary()  # For now, same as summary


class HTMLUI:
    """Render UI as HTML."""

    def __init__(self, data: Dict):
        self.data = data

    def render(self) -> str:
        """Render HTML dashboard."""
        fin = self.data.get("financial", {})
        trading = self.data.get("trading", {})
        reality = self.data.get("reality", {})
        goals = self.data.get("goals", {})
        system = self.data.get("system", {})
        actions = self.data.get("actions", {})

        status_color = {
            "CRITICAL": "#e74c3c",
            "WARNING": "#f39c12",
            "OK": "#27ae60"
        }.get(fin.get("status"), "#95a5a6")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Yair Siegel Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e; color: #eee; padding: 20px;
        }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px; border-radius: 15px; margin-bottom: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header .status {{
            display: inline-block; padding: 5px 15px; border-radius: 20px;
            background: {status_color}; font-weight: bold;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{
            background: #16213e; border-radius: 15px; padding: 20px;
            border: 1px solid #0f3460;
        }}
        .card h2 {{ color: #667eea; margin-bottom: 15px; font-size: 1.2em; }}
        .card .row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #0f3460; }}
        .card .row:last-child {{ border-bottom: none; }}
        .card .label {{ color: #888; }}
        .card .value {{ font-weight: bold; }}
        .card .value.positive {{ color: #27ae60; }}
        .card .value.negative {{ color: #e74c3c; }}
        .card .value.warning {{ color: #f39c12; }}
        .progress {{
            background: #0f3460; height: 8px; border-radius: 4px; margin-top: 5px;
        }}
        .progress-bar {{
            background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; border-radius: 4px;
        }}
        .action-item {{
            background: #0f3460; padding: 10px 15px; border-radius: 8px; margin: 5px 0;
            border-left: 3px solid #667eea;
        }}
        .timestamp {{ text-align: center; color: #666; margin-top: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>YAIR SIEGEL</h1>
            <div class="status">{fin.get('status', 'UNKNOWN')}</div>
        </div>

        <div class="grid">
            <!-- Financial -->
            <div class="card">
                <h2>💰 FINANCIAL</h2>
                <div class="row">
                    <span class="label">Liquid USD</span>
                    <span class="value">${fin.get('liquid_usd', 0):,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Deployable</span>
                    <span class="value">${fin.get('deployable', 0):,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Runway</span>
                    <span class="value {'warning' if fin.get('runway_months', 0) < 1 else ''}">{fin.get('runway_months', 0):.1f} months</span>
                </div>
                <div class="row">
                    <span class="label">Monthly Burn</span>
                    <span class="value">${fin.get('monthly_burn', 0):,.0f}</span>
                </div>
            </div>

            <!-- Trading -->
            <div class="card">
                <h2>📈 TRADING</h2>
                <div class="row">
                    <span class="label">Win Rate</span>
                    <span class="value {'positive' if trading.get('win_rate', 0) >= 0.6 else ''}">{trading.get('win_rate', 0):.1%}</span>
                </div>
                <div class="row">
                    <span class="label">Total P&L</span>
                    <span class="value {'positive' if trading.get('total_pnl', 0) >= 0 else 'negative'}">${trading.get('total_pnl', 0):+,.2f}</span>
                </div>
                <div class="row">
                    <span class="label">Resolved</span>
                    <span class="value">{trading.get('resolved', 0)} trades</span>
                </div>
                <div class="row">
                    <span class="label">Open</span>
                    <span class="value">{trading.get('open_positions', 0)} positions</span>
                </div>
            </div>

            <!-- Reality -->
            <div class="card">
                <h2>🎯 REALITY</h2>
                <div class="row">
                    <span class="label">Score</span>
                    <span class="value">{reality.get('score', 0.5):.0%}</span>
                </div>
                <div class="progress">
                    <div class="progress-bar" style="width: {reality.get('score', 0.5) * 100}%"></div>
                </div>
                <div class="row">
                    <span class="label">Urgency</span>
                    <span class="value {'warning' if reality.get('urgency') == 'CRITICAL' else ''}">{reality.get('urgency', 'NORMAL')}</span>
                </div>
                <div class="row">
                    <span class="label">Best Path</span>
                    <span class="value">{reality.get('best_future', 'Unknown')[:20]}</span>
                </div>
                <div class="row">
                    <span class="label">Expected</span>
                    <span class="value positive">${reality.get('expected_outcome', 0):+,.0f}</span>
                </div>
            </div>

            <!-- Goals -->
            <div class="card">
                <h2>📎 GOALS</h2>
                <div class="row">
                    <span class="label">Active</span>
                    <span class="value">{goals.get('active', 0)}/{goals.get('total', 0)}</span>
                </div>
                <div class="row">
                    <span class="label">Achieved</span>
                    <span class="value positive">{goals.get('achieved', 0)}</span>
                </div>
                <div class="row">
                    <span class="label">Calibration</span>
                    <span class="value">{goals.get('calibration', 0.5):.0%}</span>
                </div>
            </div>

            <!-- System -->
            <div class="card">
                <h2>⚙️ SYSTEM</h2>
                <div class="row">
                    <span class="label">Daemons</span>
                    <span class="value">{system.get('daemons', {}).get('running', 0)}/3</span>
                </div>
                <div class="row">
                    <span class="label">Bridges</span>
                    <span class="value">{system.get('bridges', 0)}</span>
                </div>
                <div class="row">
                    <span class="label">Cron Jobs</span>
                    <span class="value">{system.get('cron_jobs', 0)}</span>
                </div>
                <div class="row">
                    <span class="label">Health</span>
                    <span class="value {'positive' if system.get('health_score', 0) >= 0.9 else 'warning'}">{system.get('health_score', 0):.0%}</span>
                </div>
            </div>

            <!-- Actions -->
            <div class="card">
                <h2>⚡ ACTIONS</h2>
                {''.join(f'<div class="action-item">→ {a}</div>' for a in actions.get('immediate', [])[:3]) or '<div class="action-item">No immediate actions</div>'}
            </div>
        </div>

        <div class="timestamp">
            Updated: {self.data.get('timestamp', '')}
        </div>
    </div>
</body>
</html>"""

        return html


# =============================================================================
# MAIN UI CLASS
# =============================================================================

class YairUI:
    """
    Main UI class for Yair Siegel.

    Usage:
        ui = YairUI()
        ui.terminal()   # Print to terminal
        ui.telegram()   # Get Telegram message
        ui.html()       # Get HTML dashboard
        ui.json()       # Get JSON data
    """

    def __init__(self):
        self.aggregator = YairDataAggregator()
        self.data = None

    def refresh(self):
        """Refresh all data."""
        self.data = self.aggregator.load_all()

    def terminal(self) -> str:
        """Render and print terminal UI."""
        if not self.data:
            self.refresh()
        ui = TerminalUI(self.data)
        output = ui.render()
        print(output)
        return output

    def telegram(self) -> str:
        """Get Telegram-formatted message."""
        if not self.data:
            self.refresh()
        ui = TelegramUI(self.data)
        return ui.render_summary()

    def html(self, save_path: str = None) -> str:
        """Get HTML dashboard."""
        if not self.data:
            self.refresh()
        ui = HTMLUI(self.data)
        html = ui.render()

        if save_path:
            with open(save_path, 'w') as f:
                f.write(html)

        return html

    def json(self) -> str:
        """Get JSON data."""
        if not self.data:
            self.refresh()
        return json.dumps(self.data, indent=2)

    def get_status(self) -> Dict:
        """Get status for other bridges."""
        if not self.data:
            self.refresh()

        return {
            "bridge": "yair_ui",
            "status": "operational",
            "timestamp": self.data.get("timestamp"),
            "financial_status": self.data.get("financial", {}).get("status"),
            "reality_urgency": self.data.get("reality", {}).get("urgency"),
            "system_health": self.data.get("system", {}).get("health_score"),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_ui: Optional[YairUI] = None


def get_yair_ui() -> YairUI:
    """Get or create Yair UI."""
    global _ui
    if _ui is None:
        _ui = YairUI()
    return _ui


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Yair Siegel UI")
    parser.add_argument("format", choices=["terminal", "telegram", "html", "json", "status"],
                       default="terminal", nargs="?")
    parser.add_argument("--output", "-o", help="Output file path")
    args = parser.parse_args()

    ui = get_yair_ui()
    ui.refresh()

    if args.format == "terminal":
        ui.terminal()

    elif args.format == "telegram":
        output = ui.telegram()
        print(output)

    elif args.format == "html":
        output_path = args.output or "/tmp/yair_dashboard.html"
        ui.html(save_path=output_path)
        print(f"Dashboard saved to: {output_path}")

    elif args.format == "json":
        print(ui.json())

    elif args.format == "status":
        print(json.dumps(ui.get_status(), indent=2))


if __name__ == "__main__":
    main()
