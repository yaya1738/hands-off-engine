#!/usr/bin/env python3
"""
Real-time monitoring dashboard for AI Nexus
"""
import argparse
import time
from datetime import datetime

from audit import AuditLogger, FinancialLedger
from self_improvement import SelfImprovementEngine
from self_financing import SelfFinancingEngine


def print_dashboard(
    audit_logger: AuditLogger,
    ledger: FinancialLedger,
    session_id: str = None
):
    """Print real-time dashboard"""
    # Clear screen (works on Unix-like systems)
    print("\033[2J\033[H")

    print("="*100)
    print(" "*35 + "AI NEXUS MONITORING DASHBOARD")
    print("="*100)
    print(f"\nLast Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get session summary
    summary = audit_logger.get_session_summary(session_id)

    print(f"\n{'-'*100}")
    print("SYSTEM STATUS")
    print(f"{'-'*100}")
    print(f"Session ID:     {summary['session_id']}")
    print(f"Total Events:   {summary['total_events']}")
    print(f"Active Since:   {summary['start_time']}")

    # Financial metrics
    balance = ledger.get_balance(session_id)

    print(f"\n{'-'*100}")
    print("FINANCIAL PERFORMANCE")
    print(f"{'-'*100}")
    print(f"Total Costs:    ${balance['total_costs']:,.2f}")
    print(f"Total Revenue:  ${balance['total_revenue']:,.2f}")
    print(f"Net Profit:     ${balance['net_profit']:,.2f}")

    roi_color = "🟢" if balance['roi_percent'] > 50 else "🟡" if balance['roi_percent'] > 0 else "🔴"
    print(f"ROI:            {roi_color} {balance['roi_percent']:.2f}%")

    # Component performance
    component_perf = ledger.get_component_performance()

    if component_perf:
        print(f"\n{'-'*100}")
        print("COMPONENT PERFORMANCE")
        print(f"{'-'*100}")
        print(f"{'Component':<30} {'Cost':<15} {'Revenue':<15} {'Profit':<15} {'ROI':<10}")
        print(f"{'-'*100}")

        for component, stats in sorted(
            component_perf.items(),
            key=lambda x: x[1]['roi_percent'],
            reverse=True
        ):
            roi_indicator = "🟢" if stats['roi_percent'] > 50 else "🟡" if stats['roi_percent'] > 0 else "🔴"
            print(
                f"{component:<30} "
                f"${stats['total_cost']:>12,.2f}  "
                f"${stats['total_revenue']:>12,.2f}  "
                f"${stats['net_profit']:>12,.2f}  "
                f"{roi_indicator} {stats['roi_percent']:>6.1f}%"
            )

    # Self-improvement recommendations
    improvement_engine = SelfImprovementEngine(audit_logger, ledger)
    recommendations = improvement_engine.generate_recommendations(session_id)

    if recommendations:
        print(f"\n{'-'*100}")
        print("SELF-IMPROVEMENT RECOMMENDATIONS")
        print(f"{'-'*100}")

        for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
            priority_icon = "🔴" if rec.priority == "high" else "🟡" if rec.priority == "medium" else "🟢"
            print(f"\n{priority_icon} [{rec.priority.upper()}] {rec.title}")
            print(f"   {rec.description}")

        if len(recommendations) > 5:
            print(f"\n... and {len(recommendations) - 5} more recommendations")

    # Self-financing status
    financing_engine = SelfFinancingEngine(audit_logger, ledger)
    sustainability = financing_engine.get_sustainability_report()

    print(f"\n{'-'*100}")
    print("SELF-FINANCING STATUS")
    print(f"{'-'*100}")

    status_icon = "✅" if sustainability['is_sustainable'] else "⚠️"
    print(f"{status_icon} Status: {sustainability['sustainability_status'].replace('_', ' ').title()}")

    if sustainability['best_component']:
        print(f"\n🏆 Best Performer: {sustainability['best_component']['name']}")
        print(f"   ROI: {sustainability['best_component']['roi']:.1f}%")
        print(f"   Profit: ${sustainability['best_component']['profit']:.2f}")

    if sustainability['worst_component']:
        print(f"\n⚠️  Worst Performer: {sustainability['worst_component']['name']}")
        print(f"   ROI: {sustainability['worst_component']['roi']:.1f}%")
        print(f"   Profit: ${sustainability['worst_component']['profit']:.2f}")

    # Ledger integrity check
    print(f"\n{'-'*100}")
    print("SYSTEM INTEGRITY")
    print(f"{'-'*100}")

    is_valid = ledger.verify_integrity()
    integrity_icon = "✅" if is_valid else "❌"
    print(f"{integrity_icon} Ledger Integrity: {'VALID' if is_valid else 'COMPROMISED'}")

    print(f"\n{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Real-time monitoring dashboard for AI Nexus"
    )
    parser.add_argument(
        "--session",
        help="Monitor specific session ID"
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (no continuous monitoring)"
    )

    args = parser.parse_args()

    # Initialize systems
    audit_logger = AuditLogger()
    ledger = FinancialLedger()

    if args.once:
        print_dashboard(audit_logger, ledger, args.session)
    else:
        print("Starting AI Nexus Monitor... (Press Ctrl+C to exit)")
        try:
            while True:
                print_dashboard(audit_logger, ledger, args.session)
                time.sleep(args.refresh)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


if __name__ == "__main__":
    main()
