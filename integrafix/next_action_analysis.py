#!/usr/bin/env python3
"""
ABCFC Analysis: Next Action Decision
=====================================

Master: Yair Siegel
Context: INTEGRAFIX complete, Money Printer active, what's next?

Use Component ABCFC to score each potential action.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrafix.master_abcfc import hierarchy


def analyze_next_actions():
    """
    Analyze potential next actions using ABCFC.

    For each option, estimate:
    - Expected value (best case outcome)
    - Probability of success
    - Worst case outcome
    """

    # Load current context
    wallet = json.loads(Path('state/wallet_state.json').read_text())
    config = json.loads(Path('config/trading_config.json').read_text())
    apps = json.loads(Path('applications/job_tracker.json').read_text())

    current_capital = wallet['total_value']
    open_orders = wallet['open_orders']

    print("=" * 80)
    print("ABCFC ANALYSIS: Next Action Decision")
    print("=" * 80)
    print(f"\nCurrent Context:")
    print(f"  Capital: ${current_capital:,.2f} (${wallet['buy_total']:,.2f} BUY, ${wallet['sell_total']:,.2f} SELL)")
    print(f"  Open Orders: {open_orders}")
    print(f"  Mode: {config['mode']}")
    print(f"  Applications Ready: {apps['applications_drafted']}")
    print()

    # Define potential actions
    actions = []

    # ============================================================
    # OPTION A: Submit Job Applications
    # ============================================================
    actions.append({
        "id": "submit_job_apps",
        "name": "Submit 7 Job Applications",
        "description": "Submit pre-drafted applications to high-match companies",
        "expected_value": 150000 / 12,  # $150k/yr salary = $12.5k/mo, but need to discount by probability of any landing
        "probability": 0.30,  # 30% chance at least one responds positively (7 apps × ~5% each)
        "worst_case": -10,  # Time cost if all reject (10 hours × $0 value)
        "time_to_value": "2-8 weeks",  # Interview process
        "time_investment": "2-3 hours",  # Submit applications
        "capital_required": 0,
        "dependencies": [],
        "notes": "Apps 85-95% match, $160-250k range. SynRes 95% match. DuckDuckGo $178k+equity.",
        "data_points": {
            "applications": 7,
            "match_scores": [95, 92, 91, 90, 88, 87, 85],
            "avg_salary": 190000,
            "time_to_interview": "1-3 weeks",
            "interview_to_offer": "2-6 weeks"
        }
    })

    # ============================================================
    # OPTION B: Enhance Money Printer (More Aggressive Orders)
    # ============================================================
    actions.append({
        "id": "enhance_money_printer",
        "name": "Deploy More Aggressive Trading Orders",
        "description": "Place more fishing orders across more markets",
        "expected_value": 50,  # $50/day extra capture from more orders
        "probability": 0.40,  # 40% chance of meaningful fills in next week
        "worst_case": -25,  # Liquidity locked in bad positions
        "time_to_value": "1-7 days",  # Orders start filling immediately
        "time_investment": "3-4 hours",  # Code, test, deploy
        "capital_required": 100,  # Need more capital for more orders
        "dependencies": ["Need more trading capital"],
        "notes": "Current 6 orders = $2.2k exposure. Could 3x to $6-7k if capital available.",
        "data_points": {
            "current_orders": 6,
            "current_exposure": 2218.70,
            "potential_orders": 20,
            "potential_exposure": 7000,
            "liquidity_available": wallet['buy_total'] + wallet['sell_total']
        }
    })

    # ============================================================
    # OPTION C: Build Trading Analytics Dashboard
    # ============================================================
    actions.append({
        "id": "trading_analytics",
        "name": "Build Live Trading Analytics Dashboard",
        "description": "Real-time monitoring of fills, P&L, win rate, best strategies",
        "expected_value": 100,  # Better decisions = $100/mo value
        "probability": 0.70,  # 70% chance we build useful insights
        "worst_case": -15,  # Time cost if not useful
        "time_to_value": "Immediate (once built)",
        "time_investment": "4-6 hours",
        "capital_required": 0,
        "dependencies": [],
        "notes": "Currently blind to which strategies working. Need data to optimize.",
        "data_points": {
            "current_visibility": "Low (check logs manually)",
            "data_available": "6 open orders, historical logs",
            "potential_insights": ["Best fill prices", "Most profitable markets", "Optimal order sizes"]
        }
    })

    # ============================================================
    # OPTION D: Scale Backend Loop (More Frequent Cycles)
    # ============================================================
    actions.append({
        "id": "scale_backend_loop",
        "name": "Scale Backend Loop to Higher Frequency",
        "description": "Increase from 5min cycles to 1min cycles for faster opportunity capture",
        "expected_value": 75,  # $75/mo from faster execution
        "probability": 0.50,  # 50% chance faster cycles help
        "worst_case": -30,  # API rate limits, increased costs
        "time_to_value": "Immediate",
        "time_investment": "2-3 hours",
        "capital_required": 0,
        "dependencies": ["May need API quota increases"],
        "notes": "Current 5min cycle. Markets move fast. Faster = more opportunities.",
        "data_points": {
            "current_cycle_time": "5 minutes (300s)",
            "proposed_cycle_time": "1 minute (60s)",
            "api_calls_increase": "5x",
            "potential_api_costs": "$20-50/mo extra"
        }
    })

    # ============================================================
    # OPTION E: Hunt High-Value Bounties
    # ============================================================
    actions.append({
        "id": "hunt_bounties",
        "name": "Hunt and Complete High-Value Bounties",
        "description": "Find and complete $1000-5000 bounties from GitHub/bounty boards",
        "expected_value": 2000,  # $2000 bounty
        "probability": 0.25,  # 25% chance of completing one in reasonable time
        "worst_case": -40,  # Time invested with no payout
        "time_to_value": "1-3 weeks",
        "time_investment": "20-40 hours per bounty",
        "capital_required": 0,
        "dependencies": [],
        "notes": "Already completed $550 cortexlinux. Know the pattern.",
        "data_points": {
            "bounties_completed": 1,
            "bounty_earned": 550,
            "time_on_last": "~15 hours",
            "hourly_rate_last": 36.67,
            "available_bounties": ["Chakra $1-2k", "daydreamsai $1k"]
        }
    })

    # ============================================================
    # OPTION F: Optimize Current Fishing Orders
    # ============================================================
    actions.append({
        "id": "optimize_fishing",
        "name": "Optimize Current Fishing Order Strategy",
        "description": "Analyze current 6 orders, find better price points, better markets",
        "expected_value": 30,  # $30/mo better capture from optimization
        "probability": 0.60,  # 60% chance we find improvements
        "worst_case": -5,  # Small time cost
        "time_to_value": "1-3 days",
        "time_investment": "3-5 hours",
        "capital_required": 0,
        "dependencies": [],
        "notes": "Use current orders as data. What's working? What's not?",
        "data_points": {
            "current_orders": 6,
            "fills_to_date": 0,
            "days_active": 2,
            "need_more_data": True
        }
    })

    # ============================================================
    # OPTION G: Launch Paid Service/Product
    # ============================================================
    actions.append({
        "id": "launch_service",
        "name": "Launch Paid Polymarket Analytics Service",
        "description": "Package trading signals/analytics as paid service for other traders",
        "expected_value": 500,  # $500/mo from 10 subscribers @ $50/mo
        "probability": 0.15,  # 15% chance of getting paying customers
        "worst_case": -60,  # Time building with no customers
        "time_to_value": "4-8 weeks",
        "time_investment": "40-60 hours",
        "capital_required": 50,  # Domain, hosting, payment processing
        "dependencies": ["Need proven trading results first"],
        "notes": "High upside but need track record. Premature?",
        "data_points": {
            "our_win_rate": "62.7% (from logs)",
            "our_pnl": "$192.54 (dryrun/historical)",
            "proven_live": False,
            "market_demand": "Unknown"
        }
    })

    print("\n" + "=" * 80)
    print("ABCFC SCORING (Component Level)")
    print("=" * 80)
    print()

    risk_aversion = 0.6  # Yair's risk aversion from context

    results = []
    for action in actions:
        result = hierarchy.evaluate_opportunity(
            name=action['name'],
            expected=action['expected_value'],
            probability=action['probability'],
            worst_case=action['worst_case'],
            risk_aversion=risk_aversion
        )

        # Add action context to result
        result['action'] = action
        results.append(result)

    # Sort by ABCFC score (descending)
    results.sort(key=lambda x: x['component_level']['score'], reverse=True)

    # Display results
    print(f"{'Rank':<5} {'Action':<45} {'Score':<8} {'Decision':<10} {'EV':<12} {'Prob':<8} {'Worst':<10}")
    print("-" * 110)

    for i, result in enumerate(results, 1):
        action = result['action']
        comp = result['component_level']

        print(f"{i:<5} {action['name'][:44]:<45} {comp['score']:>7.2f} {comp['decision']:<10} "
              f"${action['expected_value']:>10.2f} {action['probability']:>6.1%} "
              f"${action['worst_case']:>8.2f}")

    print()
    print("=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        action = result['action']
        comp = result['component_level']

        print(f"\n#{i} - {action['name']}")
        print("-" * 80)
        print(f"  ABCFC Score: {comp['score']:.2f} → {comp['decision']}")
        print(f"  Expected Value: ${action['expected_value']:,.2f}")
        print(f"  Probability: {action['probability']:.1%}")
        print(f"  Worst Case: ${action['worst_case']:,.2f}")
        print(f"  Time to Value: {action['time_to_value']}")
        print(f"  Time Investment: {action['time_investment']}")
        print(f"  Capital Required: ${action['capital_required']:,.2f}")

        if action['dependencies']:
            print(f"  Dependencies: {', '.join(action['dependencies'])}")

        print(f"\n  {comp['reasoning']}")
        print(f"\n  Notes: {action['notes']}")

        # Show key data points
        if action.get('data_points'):
            print(f"\n  Data Points:")
            for k, v in action['data_points'].items():
                print(f"    • {k}: {v}")

    print("\n" + "=" * 80)
    print("MASTER ABCFC PERSPECTIVE")
    print("=" * 80)
    print("""
At the Master level (Yair Siegel), ALL of these actions feed the trajectory.

Component level says TAKE the top actions, PASS the bottom ones.
Master level says: Whether we take or pass, we're learning and progressing.

The variance is in the HOW (which actions), not the WHAT (trajectory UP).

"Can't lose. Always win. Nothing wrong."
    """)

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    # Top 3 actions
    top3 = results[:3]

    print(f"\nBased on ABCFC scoring, the top 3 actions are:")
    print()
    for i, result in enumerate(top3, 1):
        action = result['action']
        comp = result['component_level']
        print(f"{i}. {action['name']} (Score: {comp['score']:.2f})")
        print(f"   • {action['description']}")
        print(f"   • Time investment: {action['time_investment']}")
        print(f"   • Time to value: {action['time_to_value']}")
        print()

    print("Consider:")
    print("  • Parallel execution: Can we do multiple at once?")
    print("  • Sequential: Should we do highest score first?")
    print("  • Portfolio approach: Mix quick wins + long-term bets?")
    print()
    print("=" * 80)

    # Save analysis
    analysis_result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": {
            "capital": current_capital,
            "open_orders": open_orders,
            "mode": config['mode'],
            "applications_ready": apps['applications_drafted']
        },
        "risk_aversion": risk_aversion,
        "actions_analyzed": len(actions),
        "results": [
            {
                "rank": i,
                "action_id": r['action']['id'],
                "action_name": r['action']['name'],
                "abcfc_score": r['component_level']['score'],
                "decision": r['component_level']['decision'],
                "expected_value": r['action']['expected_value'],
                "probability": r['action']['probability'],
                "worst_case": r['action']['worst_case']
            }
            for i, r in enumerate(results, 1)
        ],
        "top_3": [r['action']['id'] for r in results[:3]]
    }

    output_path = Path('state/next_action_analysis.json')
    output_path.write_text(json.dumps(analysis_result, indent=2))
    print(f"Analysis saved to: {output_path}")
    print()


if __name__ == "__main__":
    analyze_next_actions()
