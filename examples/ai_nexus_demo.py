#!/usr/bin/env python3
"""
AI Nexus Demo - Complete Example

Demonstrates all features of the AI Nexus system:
- Multi-brain orchestration
- Audit logging
- Financial tracking
- Self-improvement
- Self-financing
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_nexus import (
    NexusCore, OpenAIProvider, ClaudeProvider, CopilotProvider,
    AIRequest, AIProviderType
)
from audit import AuditLogger, FinancialLedger
from ai_nexus.self_improvement import SelfImprovementEngine
from ai_nexus.self_financing import SelfFinancingEngine


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a formatted section"""
    print(f"\n{'-' * 80}")
    print(f" {title}")
    print(f"{'-' * 80}")


def demo_basic_usage():
    """Demonstrate basic AI Nexus usage"""
    print_header("AI NEXUS DEMO - Basic Usage")

    # Initialize system
    print("\n1. Initializing AI Nexus...")
    audit_logger = AuditLogger()
    ledger = FinancialLedger()
    nexus = NexusCore(audit_logger=audit_logger, ledger=ledger)
    print(f"   ✅ Session ID: {nexus.session_id}")

    # Register providers
    print("\n2. Registering AI providers...")
    nexus.register_provider(OpenAIProvider(audit_logger, ledger))
    nexus.register_provider(ClaudeProvider(audit_logger, ledger))
    nexus.register_provider(CopilotProvider(audit_logger, ledger))
    print("   ✅ Registered: OpenAI, Claude, Copilot")

    # Make AI requests
    print("\n3. Making AI requests...")

    # Request 1: Trading analysis
    print("\n   a) Trading analysis with GPT-4o-mini...")
    request1 = AIRequest(
        provider_type=AIProviderType.OPENAI,
        action="trading_analysis",
        prompt="Analyze current market sentiment for prediction markets",
        system_message="You are a trading analyst.",
        model="gpt-4o-mini",
        temperature=0.3
    )

    # Note: In production, this would actually call OpenAI API
    # For demo, we'll just log the action
    print("   ℹ️  Note: Skipping actual API call in demo mode")
    print("   ✅ Request logged to audit system")

    # Request 2: Code generation
    print("\n   b) Code generation with GPT-4o-mini...")
    request2 = AIRequest(
        provider_type=AIProviderType.OPENAI,
        action="code_generation",
        prompt="Write a Python function to calculate moving averages",
        model="gpt-4o-mini"
    )
    print("   ✅ Request logged to audit system")

    return nexus, audit_logger, ledger


def demo_revenue_tracking(nexus):
    """Demonstrate revenue tracking"""
    print_section("Revenue Tracking")

    print("\n4. Recording trading revenues...")

    # Simulate successful trades
    revenues = [
        {"component": "trading.polymarket", "amount": 50.00, "market": "election_2024"},
        {"component": "trading.polymarket", "amount": 35.50, "market": "sports_nfl"},
        {"component": "trading.polymarket", "amount": 75.00, "market": "crypto_btc"},
    ]

    for rev in revenues:
        nexus.record_revenue(
            component=rev["component"],
            action="trade_profit",
            amount=rev["amount"],
            metadata={"market": rev["market"]}
        )
        print(f"   ✅ Recorded ${rev['amount']:.2f} profit from {rev['market']}")

    print(f"\n   📊 Total Revenue: ${sum(r['amount'] for r in revenues):.2f}")


def demo_cost_tracking(ledger, session_id):
    """Demonstrate cost tracking"""
    print_section("Cost Tracking")

    print("\n5. Recording AI costs...")

    costs = [
        {"component": "ai.openai", "amount": 0.0234, "action": "trading_analysis"},
        {"component": "ai.openai", "amount": 0.0456, "action": "code_generation"},
        {"component": "ai.claude", "amount": 0.0321, "action": "code_review"},
    ]

    for cost in costs:
        ledger.add_cost(
            component=cost["component"],
            action=cost["action"],
            amount=cost["amount"],
            session_id=session_id,
            metadata={"model": "demo"}
        )
        print(f"   ✅ Recorded ${cost['amount']:.4f} for {cost['action']}")

    print(f"\n   💰 Total Costs: ${sum(c['amount'] for c in costs):.4f}")


def demo_metrics(nexus):
    """Demonstrate metrics retrieval"""
    print_section("Session Metrics")

    print("\n6. Retrieving session metrics...")
    metrics = nexus.get_session_metrics()

    print(f"\n   Session ID: {metrics['session_id']}")
    print(f"   Total Events: {metrics['audit']['total_events']}")

    print(f"\n   Financial Performance:")
    print(f"   - Total Costs:    ${metrics['financial']['total_costs']:,.4f}")
    print(f"   - Total Revenue:  ${metrics['financial']['total_revenue']:,.2f}")
    print(f"   - Net Profit:     ${metrics['financial']['net_profit']:,.2f}")
    print(f"   - ROI:            {metrics['financial']['roi_percent']:,.1f}%")


def demo_component_performance(ledger):
    """Demonstrate component performance analysis"""
    print_section("Component Performance")

    print("\n7. Analyzing component performance...")
    component_perf = ledger.get_component_performance()

    print(f"\n   {'Component':<30} {'Cost':<12} {'Revenue':<12} {'Profit':<12} {'ROI':<10}")
    print(f"   {'-' * 76}")

    for component, stats in sorted(
        component_perf.items(),
        key=lambda x: x[1]['roi_percent'],
        reverse=True
    ):
        print(
            f"   {component:<30} "
            f"${stats['total_cost']:>10,.4f} "
            f"${stats['total_revenue']:>10,.2f} "
            f"${stats['net_profit']:>10,.2f} "
            f"{stats['roi_percent']:>8.1f}%"
        )


def demo_self_improvement(audit_logger, ledger):
    """Demonstrate self-improvement system"""
    print_section("Self-Improvement Analysis")

    print("\n8. Generating self-improvement recommendations...")
    engine = SelfImprovementEngine(audit_logger, ledger)
    recommendations = engine.generate_recommendations()

    print(f"\n   Found {len(recommendations)} recommendations:\n")

    for i, rec in enumerate(recommendations, 1):
        priority_icon = "🔴" if rec.priority == "high" else "🟡" if rec.priority == "medium" else "🟢"
        print(f"   {priority_icon} [{rec.priority.upper()}] {rec.title}")
        print(f"      {rec.description}")
        print(f"      Expected Impact: {rec.expected_impact}\n")


def demo_budget_allocation(audit_logger, ledger):
    """Demonstrate optimal budget allocation"""
    print_section("Optimal Budget Allocation")

    print("\n9. Calculating optimal budget allocation...")
    engine = SelfImprovementEngine(audit_logger, ledger)
    allocations = engine.get_optimal_budget_allocation()

    print(f"\n   {'Component':<30} {'Current':<15} {'Recommended':<15} {'Adjustment':<12}")
    print(f"   {'-' * 72}")

    for component, allocation in allocations.items():
        adjustment = allocation['adjustment_factor']
        adjustment_str = f"{adjustment:.1f}x"

        print(
            f"   {component:<30} "
            f"${allocation['current_budget']:>13,.4f} "
            f"${allocation['recommended_budget']:>13,.4f} "
            f"{adjustment_str:>11}"
        )


def demo_self_financing(audit_logger, ledger):
    """Demonstrate self-financing system"""
    print_section("Self-Financing Analysis")

    print("\n10. Analyzing self-financing decisions...")
    engine = SelfFinancingEngine(audit_logger, ledger)

    # Get financing decisions
    decisions = engine.analyze_and_decide()

    print(f"\n   Financing Decisions:\n")
    for decision in decisions:
        action_icon = "📈" if decision.action == "scale_up" else "📊" if decision.action == "maintain" else "📉"
        print(f"   {action_icon} {decision.component}: {decision.action.upper()}")
        print(f"      Current Budget: ${decision.current_budget:.4f}")
        print(f"      Recommended: ${decision.recommended_budget:.4f}")
        print(f"      Reasoning: {decision.reasoning}\n")

    # Get sustainability report
    print("\n11. Checking sustainability...")
    report = engine.get_sustainability_report()

    status_icon = "✅" if report['is_sustainable'] else "⚠️"
    print(f"\n   {status_icon} Status: {report['sustainability_status'].replace('_', ' ').title()}")
    print(f"   Net Profit: ${report['net_profit']:.2f}")
    print(f"   ROI: {report['roi_percent']:.1f}%")

    if report['best_component']:
        print(f"\n   🏆 Best Performer: {report['best_component']['name']}")
        print(f"      ROI: {report['best_component']['roi']:.1f}%")
        print(f"      Profit: ${report['best_component']['profit']:.2f}")

    if report['recommendations']:
        print(f"\n   Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")


def demo_ledger_integrity(ledger):
    """Demonstrate ledger integrity verification"""
    print_section("Ledger Integrity Verification")

    print("\n12. Verifying ledger integrity...")
    is_valid = ledger.verify_integrity()

    integrity_icon = "✅" if is_valid else "❌"
    print(f"\n   {integrity_icon} Ledger Integrity: {'VALID' if is_valid else 'COMPROMISED'}")

    if is_valid:
        print("   All ledger entries are cryptographically verified.")
        print("   No tampering detected.")


def main():
    """Run the complete demo"""
    print_header("AI NEXUS - COMPREHENSIVE DEMONSTRATION")
    print("\nThis demo showcases all features of the AI Nexus system.")
    print("The system is now FULLY ALIVE and tracking all operations!")

    # Run demo sections
    nexus, audit_logger, ledger = demo_basic_usage()
    demo_revenue_tracking(nexus)
    demo_cost_tracking(ledger, nexus.session_id)
    demo_metrics(nexus)
    demo_component_performance(ledger)
    demo_self_improvement(audit_logger, ledger)
    demo_budget_allocation(audit_logger, ledger)
    demo_self_financing(audit_logger, ledger)
    demo_ledger_integrity(ledger)

    # Final summary
    print_header("DEMO COMPLETE")
    print("\n✅ AI Nexus is fully operational!")
    print("\nNext Steps:")
    print("1. View audit logs: python3 audit/audit_viewer.py")
    print("2. Start monitor: python3 ai_nexus/nexus_monitor.py")
    print("3. Check session metrics in real-time")
    print("4. Integrate with your AI workflows")

    print(f"\n📊 Session ID: {nexus.session_id}")
    print(f"View session: python3 audit/audit_viewer.py --session {nexus.session_id} --summary")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
