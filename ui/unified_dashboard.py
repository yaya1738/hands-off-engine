#!/usr/bin/env python3
"""
UNIFIED SYSTEM DASHBOARD
========================

Single interface integrating ALL system interaction points.
Works WITH the unified AI coordination architecture.

Integrates:
- Finance (balance, positions, trading)
- Hardware (cluster health, nodes)
- Coordination (agent status, messages)
- Identity (Yair Siegel verification)
- Signals (trading signals status)

Serving: Yair Siegel
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import unified AI - this dashboard serves Yair Siegel
try:
    from ai.unified_ai import MASTER, get_master, get_directive, get_system_state, get_priorities
except ImportError:
    MASTER = "Yair Siegel"
    def get_master(): return "Yair Siegel"
    def get_directive(): return {"directive": "Serve Yair Siegel"}
    def get_system_state(): return {}
    def get_priorities(): return []

app = FastAPI(title="Unified System Dashboard", description=f"Serving {MASTER}")


# ============================================================================
# DATA COLLECTORS - Pull from existing system components
# ============================================================================

def get_finance_data():
    """Collect financial data from existing finance module."""
    try:
        hub_file = REPO_ROOT / "finance" / "yair_finance_hub.json"
        if hub_file.exists():
            with open(hub_file) as f:
                hub = json.load(f)

            pm = hub.get("accounts", {}).get("polymarket", {})
            summary = hub.get("summary", {})
            credit = hub.get("credit", {})
            burn = hub.get("monthly_burn", {})

            return {
                "polymarket": {
                    "balance_usdc": pm.get("balance_usdc", 0),
                    "balance_matic": pm.get("balance_matic", 0),
                    "wallet": pm.get("wallet_address", "unknown"),
                },
                "runway": {
                    "total_liquid": summary.get("total_liquid_usd", 0),
                    "monthly_burn": burn.get("total_usd", 0),
                    "runway_months": summary.get("runway_months", 0),
                    "deployable": summary.get("deployable_to_trading", 0),
                },
                "credit": {
                    "score": credit.get("score", 0),
                    "utilization": credit.get("utilization_pct", 0),
                    "available": credit.get("total_available", 0),
                }
            }
    except Exception as e:
        pass

    return {"polymarket": {}, "runway": {}, "credit": {}, "error": str(e) if 'e' in dir() else "No data"}


def get_positions_data():
    """Get trading positions from state."""
    try:
        positions_file = REPO_ROOT / "state" / "positions.json"
        if positions_file.exists():
            with open(positions_file) as f:
                return json.load(f)
    except:
        pass
    return {"positions": [], "total_value": 0}


def get_signals_data():
    """Get trading signals from model."""
    try:
        model_file = REPO_ROOT / "state" / "polymarket-model.json"
        if model_file.exists():
            with open(model_file) as f:
                model = json.load(f)
            markets = model.get("markets", [])
            return {
                "count": len(markets),
                "avg_edge": sum(m.get("model_edge", 0) for m in markets) / len(markets) * 100 if markets else 0,
                "avg_confidence": sum(m.get("model_confidence", 0) for m in markets) / len(markets) * 100 if markets else 0,
                "top_signals": markets[:5] if markets else []
            }
    except:
        pass
    return {"count": 0, "avg_edge": 0, "avg_confidence": 0, "top_signals": []}


def get_cluster_data():
    """Get cluster health from brain state."""
    try:
        brain_file = REPO_ROOT / "state" / "brain_state.json"
        if brain_file.exists():
            with open(brain_file) as f:
                brain = json.load(f)
            return {
                "total_vcpus": brain.get("total_vcpus", 0),
                "total_ram_gb": brain.get("total_ram_gb", 0),
                "nodes": brain.get("nodes", []),
                "healthy_nodes": brain.get("healthy_nodes", 0),
                "degraded_nodes": brain.get("degraded_nodes", 0),
                "dead_nodes": brain.get("dead_nodes", 0),
                "algorithm_phase": brain.get("algorithm_phase", "unknown"),
            }
    except:
        pass
    return {"nodes": [], "healthy_nodes": 0}


def get_coordination_data():
    """Get agent coordination status."""
    try:
        status_file = REPO_ROOT / "ai" / "coordination" / "status.json"
        directive_file = REPO_ROOT / "ai" / "coordination" / "active_directive.json"

        status = {}
        directive = {}

        if status_file.exists():
            with open(status_file) as f:
                status = json.load(f)

        if directive_file.exists():
            with open(directive_file) as f:
                directive = json.load(f)

        return {
            "active_agents": status.get("active_agents", []),
            "current_phase": status.get("current_phase", "unknown"),
            "autonomous_mode": status.get("autonomous_mode", {}),
            "directive": directive.get("directive", "Serve Yair Siegel"),
            "mission": directive.get("mission", {}),
        }
    except:
        pass
    return {"active_agents": [], "directive": "Serve Yair Siegel"}


def get_identity_data():
    """Get identity verification status."""
    try:
        identity_file = REPO_ROOT / "security" / "yair_siegel_identity.json"
        if identity_file.exists():
            with open(identity_file) as f:
                return json.load(f)
    except:
        pass
    return {"verified": False, "master": MASTER}


def get_escape_velocity():
    """Calculate escape velocity score."""
    try:
        ev_file = REPO_ROOT / "state" / "escape_velocity.json"
        if ev_file.exists():
            with open(ev_file) as f:
                return json.load(f)
    except:
        pass

    # Calculate from components
    finance = get_finance_data()
    cluster = get_cluster_data()
    signals = get_signals_data()

    score = 0
    # Capital: 30%
    balance = finance.get("polymarket", {}).get("balance_usdc", 0)
    score += min(30, balance / 200 * 30)

    # Cluster: 20%
    healthy = cluster.get("healthy_nodes", 0)
    score += min(20, healthy * 4)

    # Signals: 20%
    edge = signals.get("avg_edge", 0)
    score += min(20, edge * 2)

    # Automation: 15%
    agents = len(get_coordination_data().get("active_agents", []))
    score += min(15, agents * 3.75)

    # Momentum: 15%
    score += 7.5  # Base momentum

    return {"score": round(score), "factors": {"capital": balance, "nodes": healthy, "signals": signals.get("count", 0)}}


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard HTML page."""
    return get_dashboard_html()


@app.get("/api/status")
async def api_status():
    """Complete system status API."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "master": MASTER,
        "finance": get_finance_data(),
        "positions": get_positions_data(),
        "signals": get_signals_data(),
        "cluster": get_cluster_data(),
        "coordination": get_coordination_data(),
        "identity": get_identity_data(),
        "escape_velocity": get_escape_velocity(),
        "unified_state": get_system_state(),
        "priorities": get_priorities(),
    }


@app.get("/api/finance")
async def api_finance():
    return get_finance_data()


@app.get("/api/cluster")
async def api_cluster():
    return get_cluster_data()


@app.get("/api/signals")
async def api_signals():
    return get_signals_data()


@app.get("/api/coordination")
async def api_coordination():
    return get_coordination_data()


@app.get("/api/escape-velocity")
async def api_escape_velocity():
    return get_escape_velocity()


# ============================================================================
# DASHBOARD HTML - Self-contained single-page UI
# ============================================================================

def get_dashboard_html():
    """Generate the unified dashboard HTML."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified System Dashboard - {MASTER}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header .master {{ color: #00ff88; font-size: 1.1em; }}
        .header .time {{ color: #888; font-size: 0.9em; margin-top: 10px; }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }}

        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(0,217,255,0.1);
        }}
        .card h2 {{
            color: #00d9ff;
            font-size: 1.1em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .card h2 .icon {{ font-size: 1.3em; }}

        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric .label {{ color: #888; }}
        .metric .value {{ font-weight: 600; color: #fff; }}
        .metric .value.green {{ color: #00ff88; }}
        .metric .value.red {{ color: #ff4444; }}
        .metric .value.yellow {{ color: #ffcc00; }}

        .progress-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }}
        .progress-bar .fill {{
            height: 100%;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}

        .escape-velocity {{
            background: linear-gradient(135deg, #1a1a3e 0%, #2d1a4e 100%);
            border: 2px solid #00d9ff;
        }}
        .escape-velocity .score {{
            font-size: 3em;
            text-align: center;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 20px 0;
        }}

        .node-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        .node {{
            background: rgba(0,255,136,0.1);
            border: 1px solid rgba(0,255,136,0.3);
            border-radius: 8px;
            padding: 10px;
            font-size: 0.85em;
        }}
        .node.degraded {{ background: rgba(255,204,0,0.1); border-color: rgba(255,204,0,0.3); }}
        .node.dead {{ background: rgba(255,68,68,0.1); border-color: rgba(255,68,68,0.3); }}
        .node .name {{ font-weight: 600; margin-bottom: 5px; }}
        .node .specs {{ color: #888; font-size: 0.9em; }}

        .agents {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        .agent {{
            background: rgba(0,217,255,0.2);
            border: 1px solid rgba(0,217,255,0.4);
            border-radius: 20px;
            padding: 5px 15px;
            font-size: 0.85em;
        }}
        .agent.autonomous {{ background: rgba(0,255,136,0.2); border-color: rgba(0,255,136,0.4); }}

        .signal {{
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
        }}
        .signal .question {{ font-size: 0.9em; margin-bottom: 8px; }}
        .signal .details {{ display: flex; gap: 15px; font-size: 0.85em; color: #888; }}
        .signal .details span {{ display: flex; align-items: center; gap: 5px; }}

        .refresh-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            font-size: 1.5em;
            box-shadow: 0 4px 15px rgba(0,217,255,0.4);
            transition: transform 0.2s;
        }}
        .refresh-btn:hover {{ transform: scale(1.1); }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }}
        .status-dot.green {{ background: #00ff88; box-shadow: 0 0 10px #00ff88; }}
        .status-dot.yellow {{ background: #ffcc00; box-shadow: 0 0 10px #ffcc00; }}
        .status-dot.red {{ background: #ff4444; box-shadow: 0 0 10px #ff4444; }}

        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 1.5em; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Unified System Dashboard</h1>
        <div class="master">Serving: {MASTER}</div>
        <div class="time" id="update-time">Loading...</div>
    </div>

    <div class="grid">
        <!-- Escape Velocity -->
        <div class="card escape-velocity">
            <h2><span class="icon">🚀</span> Escape Velocity</h2>
            <div class="score" id="ev-score">--</div>
            <div class="progress-bar"><div class="fill" id="ev-bar" style="width: 0%"></div></div>
            <div id="ev-factors" style="margin-top: 15px;"></div>
        </div>

        <!-- Finance -->
        <div class="card">
            <h2><span class="icon">💰</span> Finance</h2>
            <div class="metric">
                <span class="label">Polymarket Balance</span>
                <span class="value green" id="pm-balance">--</span>
            </div>
            <div class="metric">
                <span class="label">Total Liquid</span>
                <span class="value" id="total-liquid">--</span>
            </div>
            <div class="metric">
                <span class="label">Monthly Burn</span>
                <span class="value red" id="monthly-burn">--</span>
            </div>
            <div class="metric">
                <span class="label">Runway</span>
                <span class="value" id="runway">--</span>
            </div>
            <div class="metric">
                <span class="label">Credit Utilization</span>
                <span class="value" id="credit-util">--</span>
            </div>
        </div>

        <!-- Trading Signals -->
        <div class="card">
            <h2><span class="icon">📊</span> Trading Signals</h2>
            <div class="metric">
                <span class="label">Active Signals</span>
                <span class="value green" id="signal-count">--</span>
            </div>
            <div class="metric">
                <span class="label">Average Edge</span>
                <span class="value" id="avg-edge">--</span>
            </div>
            <div class="metric">
                <span class="label">Avg Confidence</span>
                <span class="value" id="avg-conf">--</span>
            </div>
            <div id="top-signals"></div>
        </div>

        <!-- Cluster Health -->
        <div class="card">
            <h2><span class="icon">🖥️</span> Compute Cluster</h2>
            <div class="metric">
                <span class="label">Total vCPUs</span>
                <span class="value" id="total-vcpus">--</span>
            </div>
            <div class="metric">
                <span class="label">Total RAM</span>
                <span class="value" id="total-ram">--</span>
            </div>
            <div class="metric">
                <span class="label">Nodes</span>
                <span class="value">
                    <span class="status-dot green"></span><span id="healthy-nodes">0</span> healthy
                </span>
            </div>
            <div class="metric">
                <span class="label">Phase</span>
                <span class="value" id="cluster-phase">--</span>
            </div>
            <div class="node-grid" id="node-grid"></div>
        </div>

        <!-- AI Coordination -->
        <div class="card">
            <h2><span class="icon">🤖</span> AI Coordination</h2>
            <div class="metric">
                <span class="label">Directive</span>
                <span class="value green" id="directive">--</span>
            </div>
            <div class="metric">
                <span class="label">Phase</span>
                <span class="value" id="coord-phase">--</span>
            </div>
            <div class="metric">
                <span class="label">Active Agents</span>
                <span class="value" id="agent-count">--</span>
            </div>
            <div class="agents" id="agents-list"></div>
        </div>

        <!-- System Priorities -->
        <div class="card">
            <h2><span class="icon">🎯</span> Unified Priorities</h2>
            <div id="priorities-list"></div>
        </div>
    </div>

    <button class="refresh-btn" onclick="loadData()">⟳</button>

    <script>
        async function loadData() {{
            try {{
                const res = await fetch('/api/status');
                const data = await res.json();

                // Update time
                document.getElementById('update-time').textContent =
                    'Last updated: ' + new Date(data.timestamp).toLocaleTimeString();

                // Escape Velocity
                const ev = data.escape_velocity || {{}};
                document.getElementById('ev-score').textContent = (ev.score || 0) + '/100';
                document.getElementById('ev-bar').style.width = (ev.score || 0) + '%';
                document.getElementById('ev-factors').innerHTML = `
                    <div class="metric"><span class="label">Capital</span><span class="value">${{(ev.factors?.capital || 0).toFixed(2)}}</span></div>
                    <div class="metric"><span class="label">Nodes</span><span class="value">{{ev.factors?.nodes || 0}}</span></div>
                    <div class="metric"><span class="label">Signals</span><span class="value">{{ev.factors?.signals || 0}}</span></div>
                `;

                // Finance
                const fin = data.finance || {{}};
                document.getElementById('pm-balance').textContent = '$' + (fin.polymarket?.balance_usdc || 0).toFixed(2);
                document.getElementById('total-liquid').textContent = '$' + (fin.runway?.total_liquid || 0).toLocaleString();
                document.getElementById('monthly-burn').textContent = '-$' + (fin.runway?.monthly_burn || 0).toLocaleString();
                document.getElementById('runway').textContent = (fin.runway?.runway_months || 0).toFixed(1) + ' months';
                document.getElementById('credit-util').textContent = (fin.credit?.utilization || 0) + '%';

                // Signals
                const sig = data.signals || {{}};
                document.getElementById('signal-count').textContent = sig.count || 0;
                document.getElementById('avg-edge').textContent = (sig.avg_edge || 0).toFixed(1) + '%';
                document.getElementById('avg-conf').textContent = (sig.avg_confidence || 0).toFixed(0) + '%';

                // Top signals
                const topSigs = sig.top_signals || [];
                document.getElementById('top-signals').innerHTML = topSigs.slice(0, 3).map(s => `
                    <div class="signal">
                        <div class="question">{{s.question?.slice(0, 60)}}...</div>
                        <div class="details">
                            <span>Side: {{s.side}}</span>
                            <span>Edge: {{(s.model_edge * 100).toFixed(1)}}%</span>
                        </div>
                    </div>
                `).join('');

                // Cluster
                const cluster = data.cluster || {{}};
                document.getElementById('total-vcpus').textContent = cluster.total_vcpus || 0;
                document.getElementById('total-ram').textContent = (cluster.total_ram_gb || 0) + ' GB';
                document.getElementById('healthy-nodes').textContent = cluster.healthy_nodes || 0;
                document.getElementById('cluster-phase').textContent = cluster.algorithm_phase || 'unknown';

                // Nodes
                const nodes = cluster.nodes || [];
                document.getElementById('node-grid').innerHTML = nodes.map(n => `
                    <div class="node {{n.status === 'healthy' ? '' : n.status === 'degraded' ? 'degraded' : 'dead'}}">
                        <div class="name">{{n.name}}</div>
                        <div class="specs">{{n.vcpus}} vCPU / {{n.ram_gb}}GB</div>
                    </div>
                `).join('');

                // Coordination
                const coord = data.coordination || {{}};
                document.getElementById('directive').textContent = 'UNIFIED';
                document.getElementById('coord-phase').textContent = coord.current_phase || 'unknown';
                document.getElementById('agent-count').textContent = coord.active_agents?.length || 0;

                // Agents
                const agents = coord.active_agents || [];
                const autoMode = coord.autonomous_mode || {{}};
                document.getElementById('agents-list').innerHTML = agents.map(a => `
                    <span class="agent {{autoMode[a] ? 'autonomous' : ''}}">{{a}}</span>
                `).join('');

                // Priorities
                const priorities = data.priorities || [];
                document.getElementById('priorities-list').innerHTML = priorities.map(p => `
                    <div class="metric"><span class="value">{{p}}</span></div>
                `).join('');

            }} catch (err) {{
                console.error('Failed to load data:', err);
            }}
        }}

        // Load data on start and refresh every 30 seconds
        loadData();
        setInterval(loadData, 30000);
    </script>
</body>
</html>'''


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(f"Unified System Dashboard")
    print(f"========================")
    print(f"Serving: {MASTER}")
    print(f"Access: http://localhost:8002")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")
