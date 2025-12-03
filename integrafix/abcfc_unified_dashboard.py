#!/usr/bin/env python3
"""
INTEGRAFIX: ABCFC Unified Dashboard
===================================

Single dashboard showing complete ABCFC state with all integrations.

DISPLAYS:
=========
1. HIERARCHY - Full Yair Siegel ABCFC tree
2. NEXUS CLOUD - Decision space with all futures
3. RISK PROFILE - Active risk modifiers and adjusted bounds
4. REALITY - Current financial state from all bridges
5. RECOMMENDATION - Best action with rationale
6. HISTORY - Recent decisions and outcomes

OUTPUT FORMATS:
===============
- Terminal (rich text)
- HTML (web dashboard)
- JSON (API)
- Telegram (markdown)

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


class ABCFCUnifiedDashboard:
    """
    Unified dashboard for ABCFC system.

    Aggregates all ABCFC components into single view.
    """

    def __init__(self):
        self._orchestrator = None
        self._data = None

    def _load_orchestrator(self):
        """Load ABCFC orchestrator."""
        if self._orchestrator is None:
            try:
                from integrafix.abcfc_orchestrator import ABCFCOrchestrator
                self._orchestrator = ABCFCOrchestrator()
                self._orchestrator.observe()
            except Exception as e:
                print(f"Warning: Could not load orchestrator: {e}")
        return self._orchestrator

    def load_data(self) -> Dict:
        """Load all dashboard data."""
        orch = self._load_orchestrator()
        if orch:
            self._data = orch.get_dashboard_data()
        else:
            self._data = {"error": "Orchestrator not available"}
        return self._data

    # =========================================================================
    # TERMINAL OUTPUT
    # =========================================================================

    def render_terminal(self) -> str:
        """Render dashboard for terminal."""
        if self._data is None:
            self.load_data()

        data = self._data
        lines = []

        # Header
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + "YAIR SIEGEL ABCFC DASHBOARD".center(68) + "║")
        lines.append("║" + f"Generated: {data.get('timestamp', 'N/A')[:19]}".center(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # Mode and Risk
        mode = data.get('mode', 'DRY_RUN')
        risk = data.get('risk_aversion', 0.6)
        lines.append("║" + f"  Mode: {mode:12}  Risk Aversion: {risk:.1f}".ljust(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # Hierarchy
        hier = data.get('hierarchy', {})
        lines.append("║  HIERARCHY".ljust(69) + "║")
        lines.append("║" + f"    Nodes: {hier.get('nodes', 0)}".ljust(68) + "║")
        bounds = hier.get('bounds', (0, 0))
        lines.append("║" + f"    Bounds: [{bounds[0]:+,.0f}, {bounds[1]:+,.0f}]".ljust(68) + "║")
        lines.append("║" + f"    Expected: {hier.get('expected', 0):+,.0f}".ljust(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # Risk Adjustments
        risk_data = data.get('risk', {})
        lines.append("║  RISK ADJUSTMENTS".ljust(69) + "║")
        mods = risk_data.get('modifiers', [])
        if mods:
            for m in mods[:3]:
                lines.append("║" + f"    • {m}".ljust(68) + "║")
            if len(mods) > 3:
                lines.append("║" + f"    + {len(mods) - 3} more...".ljust(68) + "║")
        lines.append("║" + f"    Adjusted Worst: {risk_data.get('adjusted_worst', 0):+,.0f}".ljust(68) + "║")
        lines.append("║" + f"    Adjusted Expected: {risk_data.get('adjusted_expected', 0):+,.0f}".ljust(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # Nexus Cloud
        nexus = data.get('nexus', {})
        lines.append("║  NEXUS CLOUD".ljust(69) + "║")
        lines.append("║" + f"    Futures Evaluated: {nexus.get('cloud_size', 0)}".ljust(68) + "║")
        cb = nexus.get('cloud_bounds', {})
        if cb:
            lines.append("║" + f"    Cloud Bounds: [{cb.get('worst_possible', 0):+,.0f}, {cb.get('best_possible', 0):+,.0f}]".ljust(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # Recommendation
        rec = data.get('recommendation', {})
        lines.append("║  RECOMMENDATION".ljust(69) + "║")
        lines.append("║" + f"    Action: {rec.get('action', 'hold')} on {rec.get('node', 'root')}".ljust(68) + "║")
        lines.append("║" + f"    Score: {rec.get('score', 0):.1f}".ljust(68) + "║")
        lines.append("╠" + "═" * 68 + "╣")

        # Reality
        reality = data.get('reality', {})
        if reality and 'error' not in reality:
            lines.append("║  REALITY".ljust(69) + "║")
            lines.append("║" + f"    Liquid: ${reality.get('liquid_usd', 0):,.0f}".ljust(68) + "║")
            lines.append("║" + f"    Deployable: ${reality.get('deployable', 0):,.0f}".ljust(68) + "║")
            lines.append("║" + f"    Runway: {reality.get('runway_months', 0):.1f} months".ljust(68) + "║")
            lines.append("║" + f"    Win Rate: {reality.get('win_rate', 0):.1%}".ljust(68) + "║")
            lines.append("╠" + "═" * 68 + "╣")

        # Sources
        sources = data.get('sources', [])
        lines.append("║  SOURCES LOADED".ljust(69) + "║")
        for src in sources:
            lines.append("║" + f"    ✓ {src}".ljust(68) + "║")

        lines.append("╚" + "═" * 68 + "╝")

        return "\n".join(lines)

    # =========================================================================
    # HTML OUTPUT
    # =========================================================================

    def render_html(self, save_path: str = None) -> str:
        """Render dashboard as HTML."""
        if self._data is None:
            self.load_data()

        data = self._data
        hier = data.get('hierarchy', {})
        risk_data = data.get('risk', {})
        nexus = data.get('nexus', {})
        rec = data.get('recommendation', {})
        reality = data.get('reality', {})
        cb = nexus.get('cloud_bounds', {})

        # Determine status color
        exp = hier.get('expected', 0)
        adj_exp = risk_data.get('adjusted_expected', 0)
        if adj_exp < 0:
            status_color = "#e74c3c"
            status_text = "CRITICAL"
        elif adj_exp < 500:
            status_color = "#f39c12"
            status_text = "WARNING"
        else:
            status_color = "#27ae60"
            status_text = "STABLE"

        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>ABCFC Dashboard - Yair Siegel</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee; padding: 20px; min-height: 100vh;
        }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px; border-radius: 15px; margin-bottom: 20px;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .header h1 {{ font-size: 1.8em; }}
        .header .status {{
            padding: 10px 20px; border-radius: 25px;
            background: {status_color}; font-weight: bold; font-size: 1.2em;
        }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }}
        .card {{
            background: #16213e; border-radius: 15px; padding: 20px;
            border: 1px solid #0f3460;
        }}
        .card h2 {{ color: #667eea; margin-bottom: 15px; font-size: 1.1em; }}
        .card .row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #0f3460; }}
        .card .row:last-child {{ border-bottom: none; }}
        .card .label {{ color: #888; }}
        .card .value {{ font-weight: bold; font-family: monospace; }}
        .card .value.positive {{ color: #27ae60; }}
        .card .value.negative {{ color: #e74c3c; }}
        .card .value.warning {{ color: #f39c12; }}
        .recommendation {{
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            border: 2px solid #667eea;
        }}
        .action-box {{
            background: #667eea; padding: 15px; border-radius: 10px;
            text-align: center; margin-top: 10px;
        }}
        .action-box .action-name {{ font-size: 1.3em; font-weight: bold; }}
        .progress {{
            background: #0f3460; height: 10px; border-radius: 5px; margin-top: 10px; overflow: hidden;
        }}
        .progress-bar {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%; border-radius: 5px;
        }}
        .cloud-vis {{
            display: flex; justify-content: space-between; margin-top: 15px;
        }}
        .cloud-bound {{
            text-align: center; padding: 10px; border-radius: 8px;
        }}
        .cloud-bound.worst {{ background: rgba(231, 76, 60, 0.2); }}
        .cloud-bound.best {{ background: rgba(39, 174, 96, 0.2); }}
        .sources {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
        .source {{
            background: #0f3460; padding: 5px 12px; border-radius: 15px;
            font-size: 0.85em;
        }}
        .timestamp {{ text-align: center; color: #666; margin-top: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div>
                <h1>ABCFC DASHBOARD</h1>
                <div style="opacity: 0.8; margin-top: 5px;">Yair Siegel Financial Decision System</div>
            </div>
            <div class="status">{status_text}</div>
        </div>

        <div class="grid">
            <!-- Hierarchy -->
            <div class="card">
                <h2>📊 HIERARCHY</h2>
                <div class="row">
                    <span class="label">Nodes</span>
                    <span class="value">{hier.get('nodes', 0)}</span>
                </div>
                <div class="row">
                    <span class="label">Worst Case</span>
                    <span class="value negative">${hier.get('bounds', (0,0))[0]:+,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Best Case</span>
                    <span class="value positive">${hier.get('bounds', (0,0))[1]:+,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Expected</span>
                    <span class="value {'positive' if hier.get('expected', 0) > 0 else 'negative'}">${hier.get('expected', 0):+,.0f}</span>
                </div>
            </div>

            <!-- Risk Adjustments -->
            <div class="card">
                <h2>⚠️ RISK PROFILE</h2>
                <div class="row">
                    <span class="label">Active Modifiers</span>
                    <span class="value warning">{len(risk_data.get('modifiers', []))}</span>
                </div>
                <div class="row">
                    <span class="label">Adjusted Worst</span>
                    <span class="value negative">${risk_data.get('adjusted_worst', 0):+,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Adjusted Expected</span>
                    <span class="value {'positive' if risk_data.get('adjusted_expected', 0) > 0 else 'negative'}">${risk_data.get('adjusted_expected', 0):+,.0f}</span>
                </div>
                <div style="margin-top: 10px; font-size: 0.85em; color: #888;">
                    {', '.join(risk_data.get('modifiers', [])[:3]) or 'None'}
                </div>
            </div>

            <!-- Nexus Cloud -->
            <div class="card">
                <h2>☁️ NEXUS CLOUD</h2>
                <div class="row">
                    <span class="label">Futures Evaluated</span>
                    <span class="value">{nexus.get('cloud_size', 0)}</span>
                </div>
                <div class="cloud-vis">
                    <div class="cloud-bound worst">
                        <div style="font-size: 0.8em; color: #888;">Worst</div>
                        <div style="font-weight: bold; color: #e74c3c;">${cb.get('worst_possible', 0):+,.0f}</div>
                    </div>
                    <div class="cloud-bound" style="background: rgba(102, 126, 234, 0.2);">
                        <div style="font-size: 0.8em; color: #888;">Expected</div>
                        <div style="font-weight: bold;">${cb.get('best_expected', 0):+,.0f}</div>
                    </div>
                    <div class="cloud-bound best">
                        <div style="font-size: 0.8em; color: #888;">Best</div>
                        <div style="font-weight: bold; color: #27ae60;">${cb.get('best_possible', 0):+,.0f}</div>
                    </div>
                </div>
            </div>

            <!-- Reality -->
            <div class="card">
                <h2>💰 REALITY</h2>
                <div class="row">
                    <span class="label">Liquid USD</span>
                    <span class="value">${reality.get('liquid_usd', 0):,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Deployable</span>
                    <span class="value">${reality.get('deployable', 0):,.0f}</span>
                </div>
                <div class="row">
                    <span class="label">Runway</span>
                    <span class="value {'warning' if reality.get('runway_months', 0) < 1 else ''}">{reality.get('runway_months', 0):.1f} mo</span>
                </div>
                <div class="row">
                    <span class="label">Win Rate</span>
                    <span class="value positive">{reality.get('win_rate', 0):.1%}</span>
                </div>
            </div>

            <!-- Recommendation -->
            <div class="card recommendation" style="grid-column: span 2;">
                <h2>🎯 RECOMMENDED ACTION</h2>
                <div class="action-box">
                    <div class="action-name">{rec.get('action', 'hold').upper()}</div>
                    <div style="opacity: 0.8;">on {rec.get('node', 'root')}</div>
                </div>
                <div class="row" style="margin-top: 15px;">
                    <span class="label">Score</span>
                    <span class="value">{rec.get('score', 0):.1f}</span>
                </div>
                <div class="row">
                    <span class="label">Risk Aversion</span>
                    <span class="value">{data.get('risk_aversion', 0.6):.1f}</span>
                </div>
                <div class="row">
                    <span class="label">Mode</span>
                    <span class="value">{data.get('mode', 'DRY_RUN')}</span>
                </div>
            </div>
        </div>

        <!-- Sources -->
        <div class="card" style="margin-top: 20px;">
            <h2>🔗 INTEGRATED SOURCES</h2>
            <div class="sources">
                {''.join(f'<span class="source">✓ {s}</span>' for s in data.get('sources', []))}
            </div>
        </div>

        <div class="timestamp">
            Updated: {data.get('timestamp', 'N/A')}
        </div>
    </div>
</body>
</html>'''

        if save_path:
            with open(save_path, 'w') as f:
                f.write(html)

        return html

    # =========================================================================
    # JSON OUTPUT
    # =========================================================================

    def render_json(self) -> str:
        """Render dashboard as JSON."""
        if self._data is None:
            self.load_data()
        return json.dumps(self._data, indent=2)

    # =========================================================================
    # TELEGRAM OUTPUT
    # =========================================================================

    def render_telegram(self) -> str:
        """Render dashboard for Telegram markdown."""
        if self._data is None:
            self.load_data()

        data = self._data
        hier = data.get('hierarchy', {})
        risk_data = data.get('risk', {})
        nexus = data.get('nexus', {})
        rec = data.get('recommendation', {})
        reality = data.get('reality', {})

        lines = [
            "*ABCFC DASHBOARD*",
            f"_Yair Siegel | {data.get('mode', 'DRY_RUN')}_",
            "",
            "📊 *Hierarchy*",
            f"└ Bounds: `[{hier.get('bounds', (0,0))[0]:+,.0f}, {hier.get('bounds', (0,0))[1]:+,.0f}]`",
            f"└ Expected: `{hier.get('expected', 0):+,.0f}`",
            "",
            "⚠️ *Risk Profile*",
            f"└ Modifiers: {len(risk_data.get('modifiers', []))}",
            f"└ Adj Expected: `{risk_data.get('adjusted_expected', 0):+,.0f}`",
            "",
            "☁️ *Nexus Cloud*",
            f"└ Futures: {nexus.get('cloud_size', 0)}",
            "",
            "🎯 *Recommendation*",
            f"└ `{rec.get('action', 'hold').upper()}` on {rec.get('node', 'root')}",
            f"└ Score: {rec.get('score', 0):.1f}",
            "",
            "💰 *Reality*",
            f"└ Deployable: `${reality.get('deployable', 0):,.0f}`",
            f"└ Runway: `{reality.get('runway_months', 0):.1f}` mo",
        ]

        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ABCFC Unified Dashboard")
    parser.add_argument("format", choices=["terminal", "html", "json", "telegram"],
                       default="terminal", nargs="?")
    parser.add_argument("--save", help="Save HTML to path")
    args = parser.parse_args()

    dashboard = ABCFCUnifiedDashboard()

    if args.format == "terminal":
        print(dashboard.render_terminal())

    elif args.format == "html":
        save_path = args.save or "/tmp/abcfc_dashboard.html"
        html = dashboard.render_html(save_path=save_path)
        print(f"Dashboard saved to: {save_path}")

    elif args.format == "json":
        print(dashboard.render_json())

    elif args.format == "telegram":
        print(dashboard.render_telegram())


if __name__ == "__main__":
    main()
