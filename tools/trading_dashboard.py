#!/usr/bin/env python3
"""
Real-Time Trading Dashboard
Analyzes current execution plan and provides actionable insights
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from decider.ho_decider import Decider


def load_execution_plan():
    """Load current execution plan"""
    plan_path = REPO_ROOT / "executor" / "execution_plan.json"
    if not plan_path.exists():
        return None

    with open(plan_path, 'r') as f:
        return json.load(f)


def load_polymarket_model():
    """Load polymarket model data"""
    model_path = REPO_ROOT / "state" / "polymarket-model.json"
    if not model_path.exists():
        return None

    with open(model_path, 'r') as f:
        return json.load(f)


def analyze_markets(decider, model_data):
    """Analyze markets with current filtering"""
    markets = model_data.get('markets', [])

    analysis = {
        'total': len(markets),
        'expired': 0,
        'tradeable': 0,
        'low_confidence': 0,
        'time_decay_applied': 0,
        'markets': []
    }

    for market in markets:
        market_analysis = {
            'id': market['market_id'],
            'question': market['question'],
            'edge': market['model_edge'],
            'confidence': market['model_confidence'],
            'side': market['side'],
            'market_price': market['market_price'],
        }

        # Check expiration
        is_expired = decider.is_market_expired(market['question'])
        days_remaining = decider.get_days_to_expiration(market['question'])

        market_analysis['expired'] = is_expired
        market_analysis['days_remaining'] = days_remaining

        if is_expired:
            analysis['expired'] += 1
            market_analysis['status'] = '❌ EXPIRED'
        elif market['model_confidence'] < 0.60:
            analysis['low_confidence'] += 1
            market_analysis['status'] = '❌ LOW CONFIDENCE'
        else:
            analysis['tradeable'] += 1
            if days_remaining < 7:
                analysis['time_decay_applied'] += 1
                market_analysis['status'] = '✅ TRADEABLE (time decay)'
            else:
                market_analysis['status'] = '✅ TRADEABLE'

        analysis['markets'].append(market_analysis)

    return analysis


def print_dashboard():
    """Print comprehensive trading dashboard"""

    print("=" * 80)
    print("HANDS-OFF ENGINE - TRADING DASHBOARD")
    print("=" * 80)
    print()

    # Load data
    execution_plan = load_execution_plan()
    model_data = load_polymarket_model()

    # Current time
    now = datetime.now(timezone.utc)
    print(f"📅 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # Execution Plan Status
    if execution_plan:
        print("🎯 EXECUTION PLAN STATUS")
        print("-" * 80)

        as_of = datetime.fromisoformat(execution_plan['as_of'].replace('Z', '+00:00'))
        age_minutes = (now - as_of).total_seconds() / 60

        age_status = "🟢 FRESH" if age_minutes < 60 else "🟡 AGING" if age_minutes < 120 else "🔴 STALE"

        print(f"Generated:        {as_of.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Age:              {age_status} ({age_minutes:.1f} minutes old)")
        print(f"Mode:             {execution_plan['mode']}")
        print(f"Live Enabled:     {'✅' if execution_plan['live_enabled'] else '❌'} {execution_plan['live_enabled']}")
        print(f"Health Status:    {execution_plan['health_status'].upper()}")
        print(f"Gate Blocked:     {'🔴 YES' if execution_plan['gate_blocked'] else '🟢 NO'}")
        print(f"Killswitch:       {'🔴 ACTIVE' if execution_plan['killswitch_present'] else '🟢 NOT PRESENT'}")
        print()

        print(f"Orders in Plan:   {execution_plan['orders_in_plan']}")
        print(f"Live USD:         ${execution_plan['total_live_usd']:.2f}")
        print(f"Demo USD:         ${execution_plan['total_demo_usd']:.2f}")
        print()

        print(f"Max Daily USD:    ${execution_plan['max_live_daily_usd']:.2f}")
        print(f"Max Per Order:    ${execution_plan['max_live_per_order_usd']:.2f}")
        print(f"Live Fraction:    {execution_plan['live_fraction']:.0%}")
        print()
    else:
        print("⚠️  No execution plan found")
        print()

    # Model Analysis
    if model_data:
        print("📊 MARKET ANALYSIS")
        print("-" * 80)

        model_time = datetime.fromisoformat(model_data['generated_at'].replace('Z', '+00:00'))
        model_age_hours = (now - model_time).total_seconds() / 3600

        model_status = "🟢 FRESH" if model_age_hours < 4 else "🟡 AGING" if model_age_hours < 12 else "🔴 STALE"

        print(f"Model Generated:  {model_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Model Age:        {model_status} ({model_age_hours:.1f} hours old)")
        print()

        # Analyze with decider
        decider = Decider(bankroll=1000.0, filter_expired=True, apply_time_decay=True)
        analysis = analyze_markets(decider, model_data)

        print(f"Total Markets:    {analysis['total']}")
        print(f"✅ Tradeable:     {analysis['tradeable']}")
        print(f"❌ Expired:       {analysis['expired']}")
        print(f"❌ Low Confidence: {analysis['low_confidence']}")
        print(f"⏰ Time Decay:    {analysis['time_decay_applied']}")
        print()

        # Market details
        print("📈 MARKET OPPORTUNITIES")
        print("-" * 80)
        print(f"{'Status':<25} {'Edge':<8} {'Conf':<8} {'Days':<8} {'Market':<30}")
        print("-" * 80)

        for market in sorted(analysis['markets'], key=lambda x: x['edge'], reverse=True):
            status_emoji = market['status'][:2]
            edge_pct = f"{market['edge']:.1%}"
            conf_pct = f"{market['confidence']:.0%}"
            days = f"{market['days_remaining']:.1f}d" if not market['expired'] else "EXP"

            # Truncate question
            question = market['question']
            if len(question) > 40:
                question = question[:37] + "..."

            print(f"{status_emoji} {market['status']:<22} {edge_pct:<8} {conf_pct:<8} {days:<8} {question}")

        print()

        # Expected value calculation
        if analysis['tradeable'] > 0:
            print("💰 EXPECTED VALUE")
            print("-" * 80)

            total_ev = 0
            total_risk = 0

            for market in analysis['markets']:
                if '✅' in market['status']:
                    # Base position size (Kelly)
                    edge = market['edge']
                    confidence = market['confidence']
                    kelly = edge * confidence
                    position = min(kelly * 1000, 100)  # Max $100

                    # Apply confidence scaling (60-70%)
                    if confidence < 0.70:
                        position *= (confidence / 0.70)

                    # Apply time decay
                    if market['days_remaining'] < 1:
                        position = 0
                    elif market['days_remaining'] < 3:
                        position *= 0.5
                    elif market['days_remaining'] < 7:
                        position *= 0.75

                    ev = position * edge
                    total_ev += ev
                    total_risk += position

            print(f"Total Risk:       ${total_risk:.2f}")
            print(f"Total EV (100%):  ${total_ev:.2f}")
            print(f"Total EV (70%):   ${total_ev * 0.70:.2f} (after edge capture)")
            print(f"ROI:              {(total_ev / total_risk * 100) if total_risk > 0 else 0:.1f}%")
            print()
    else:
        print("⚠️  No model data found")
        print()

    # Recommendations
    print("🎯 RECOMMENDATIONS")
    print("-" * 80)

    recommendations = []

    if execution_plan:
        # Check plan age
        if age_minutes > 120:
            recommendations.append("🔴 URGENT: Regenerate execution plan (>120 min old)")
        elif age_minutes > 60:
            recommendations.append("🟡 Consider regenerating execution plan (>60 min old)")

        # Check mode
        if execution_plan['mode'] == 'DRYRUN' and execution_plan.get('requested_mode') == 'LIVE':
            recommendations.append("⚠️  Mode mismatch: Plan is DRYRUN but LIVE requested")

        # Check health
        if execution_plan['health_status'] != 'healthy':
            recommendations.append(f"⚠️  Health degraded: {execution_plan['health_status']}")

        # Check orders
        if execution_plan['orders_in_plan'] == 0 and analysis and analysis['tradeable'] > 0:
            recommendations.append("💡 No orders in plan despite tradeable markets - regenerate?")

    if model_data and model_age_hours > 12:
        recommendations.append("🔴 Model data is stale (>12 hours) - refresh data")
    elif model_data and model_age_hours > 4:
        recommendations.append("🟡 Model data aging (>4 hours) - consider refresh")

    if analysis and analysis['tradeable'] > 0:
        if analysis['tradeable'] < 3:
            recommendations.append("💡 Low market count - expand coverage (sports, macro, politics)")

        if analysis['time_decay_applied'] > 0:
            recommendations.append(f"⏰ {analysis['time_decay_applied']} markets have time decay - find December+ markets")

    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  ✅ All systems optimal!")

    print()
    print("=" * 80)


if __name__ == "__main__":
    print_dashboard()
