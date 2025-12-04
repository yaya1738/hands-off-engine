#!/usr/bin/env python3
"""
Test Autonomous Payment Flow
Verifies that offers are evaluated and responded to autonomously.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from autonomous.payment_automation import PaymentAutomation


def test_offer_scenarios():
    """Test different offer scenarios."""
    automation = PaymentAutomation()

    print("=" * 70)
    print("AUTONOMOUS PAYMENT SYSTEM - TEST SCENARIOS")
    print("=" * 70)

    # Scenario 1: High offer - should auto-accept
    print("\n[TEST 1] High Offer: $200,000")
    print("-" * 70)
    result = automation.handle_job_offer(
        company="Pydantic",
        salary=200000,
        details={
            "contact_email": "careers@pydantic.dev",
            "start_date": "2025-01-15",
            "remote": True
        }
    )
    print(f"Decision: {result['decision']}")
    print(f"Annual Income: ${result.get('annual_income', 0):,.0f}")
    print(f"Monthly Income: ${result.get('monthly_income', 0):,.0f}")
    assert result['decision'] == 'accepted', "Should auto-accept $200k+"

    # Scenario 2: Mid-range offer - should negotiate
    print("\n[TEST 2] Mid-Range Offer: $175,000")
    print("-" * 70)
    result = automation.handle_job_offer(
        company="Beautiful.ai",
        salary=175000,
        details={
            "contact_email": "careers@beautiful.ai",
            "start_date": "2025-02-01",
            "remote": True
        }
    )
    print(f"Decision: {result['decision']}")
    print(f"Counter Offer: ${result.get('counter_offer', 0):,.0f}")
    print(f"Original: ${result.get('original_offer', 0):,.0f}")
    assert result['decision'] == 'negotiating', "Should negotiate $150-200k"

    # Scenario 3: Low offer - should reject
    print("\n[TEST 3] Low Offer: $120,000")
    print("-" * 70)
    result = automation.handle_job_offer(
        company="LowBall Inc",
        salary=120000,
        details={
            "contact_email": "hr@lowball.com",
            "start_date": "2025-01-01",
            "remote": False
        }
    )
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result.get('reason', 'N/A')}")
    assert result['decision'] == 'rejected', "Should reject <$150k"

    # Check income summary
    print("\n[INCOME SUMMARY]")
    print("-" * 70)
    summary = automation.get_income_summary()
    print(f"Total Received: ${summary['total_received']:,.0f}")
    print(f"Pending: ${summary['pending']:,.0f}")
    print(f"Active Streams: {summary['active_streams']}")
    print(f"Monthly Projection: ${summary['monthly_projection']:,.0f}")
    print(f"Annual Projection: ${summary['annual_projection']:,.0f}")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - AUTONOMOUS PAYMENT SYSTEM WORKING")
    print("=" * 70)


if __name__ == "__main__":
    test_offer_scenarios()
