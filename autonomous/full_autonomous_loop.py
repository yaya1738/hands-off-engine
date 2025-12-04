#!/usr/bin/env python3
"""
Full Autonomous Loop - API Powered
===================================

The COMPLETE autonomous system powered by API orchestrator:

1. Scans for bounties via GitHub API
2. Checks markets via Polymarket API
3. Monitors bugs via HackerOne API
4. Tracks wallet via blockchain APIs
5. All operations use ABCFC-optimized API calls

ZERO HUMAN INTERACTION REQUIRED.
All operations through unified API system.

Master: Yair Siegel
Progress = Less dependency on human
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Add integrafix to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from integrafix.api_orchestrator import APIOrchestrator


class AutonomousLoop:
    """Full autonomous operation loop using API orchestrator."""

    def __init__(self):
        self.running = True
        self.orchestrator = APIOrchestrator()
        self.wallet_address = "0xB314345D218ED4CF75C17636a2307244E7dA761b"

    def run_v1_money_printer(self):
        """V1: Money Printer - Check markets via API."""
        print("\n🖨️  [V1: MONEY PRINTER]")
        try:
            result = self.orchestrator.get_polymarket_markets()
            if result.success:
                market_count = len(result.data)
                print(f"✅ Found {market_count} active markets")
                print(f"   ABCFC Score: {result.abcfc_score:.2f}")
                print(f"   Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")
                return True
            else:
                print(f"❌ Failed: {result.error}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def run_v2_bounty_hunter(self):
        """V2: GitHub Bounty Hunter - Search via API."""
        print("\n🎯 [V2: GITHUB BOUNTY HUNTER]")
        try:
            result = self.orchestrator.search_github_bounties(
                query="label:bounty is:open",
                per_page=30
            )
            if result.success:
                bounties = result.data.get("parsed_bounties", [])
                print(f"✅ Found {len(bounties)} bounties")
                print(f"   ABCFC Score: {result.abcfc_score:.2f}")
                print(f"   Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")

                # Show top 3 bounties
                if bounties:
                    print("   Top bounties:")
                    for i, bounty in enumerate(bounties[:3], 1):
                        repo_str = "/".join(bounty["repo"])
                        amount_str = f"${bounty['amount']:.0f}" if bounty['amount'] > 0 else "Amount TBD"
                        print(f"   {i}. {repo_str} #{bounty['issue_number']} - {amount_str}")

                return True
            else:
                print(f"❌ Failed: {result.error}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def run_v3_bug_bounty_hunter(self):
        """V3: Bug Bounty Hunter - Check programs via API."""
        print("\n🔒 [V3: BUG BOUNTY HUNTER]")
        try:
            result = self.orchestrator.list_bug_bounty_programs()
            if result.success:
                print(f"✅ Programs checked via API")
                print(f"   ABCFC Score: {result.abcfc_score:.2f}")
                print(f"   Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")
                return True
            else:
                # Expected if no credentials
                print(f"⚠️  {result.error}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def check_wallet_balance(self):
        """Check crypto wallet balance via API."""
        print("\n💰 [WALLET CHECK]")
        try:
            # Check Ethereum
            result = self.orchestrator.check_wallet_balance(
                self.wallet_address,
                network="ethereum"
            )
            if result.success:
                print(f"✅ Ethereum wallet checked")
                print(f"   ABCFC Score: {result.abcfc_score:.2f}")
                print(f"   Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")
                return True
            else:
                print(f"⚠️  {result.error}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def run_cycle(self):
        """Run one complete autonomous cycle via APIs."""
        print("=" * 80)
        print(f"🤖 AUTONOMOUS CYCLE (API-POWERED) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        results = {
            "v1_money_printer": False,
            "v2_bounty_hunter": False,
            "v3_bug_bounty": False,
            "wallet_check": False
        }

        # Run all verticals via API orchestrator
        results["v1_money_printer"] = self.run_v1_money_printer()
        results["v2_bounty_hunter"] = self.run_v2_bounty_hunter()
        results["v3_bug_bounty"] = self.run_v3_bug_bounty_hunter()
        results["wallet_check"] = self.check_wallet_balance()

        # Show API statistics
        print("\n📊 [API STATISTICS]")
        api_stats = self.orchestrator.api_manager.get_api_stats()
        print(f"✅ Total API Calls: {api_stats['total_calls']}")
        print(f"   Success Rate: {api_stats['success_rate']:.1%}")
        print(f"   Total Cost: ${api_stats['total_cost']:.4f}")
        print(f"   Net Value: ${api_stats['net_value']:.2f}")
        if api_stats['roi'] != float('inf'):
            print(f"   ROI: {api_stats['roi']:.1f}x")
        else:
            print(f"   ROI: ∞ (zero cost)")

        print()
        print("=" * 80)
        success_count = sum(1 for v in results.values() if v)
        print(f"✅ Cycle complete - {success_count}/{len(results)} operations successful")
        print("=" * 80)
        print()

        return results

    def run_forever(self):
        """Run the autonomous loop forever via APIs."""
        print("🚀 FULL AUTONOMOUS MODE (API-POWERED)")
        print("=" * 80)
        print()
        print("Operating via unified API system:")
        print("  • V1: Money Printer → Polymarket API")
        print("  • V2: GitHub Bounty Hunter → GitHub API")
        print("  • V3: Bug Bounty Hunter → HackerOne API")
        print("  • Infrastructure → Blockchain APIs")
        print()
        print("All operations use ABCFC-optimized API calls")
        print()
        print("Press Ctrl+C to stop")
        print()

        cycle_count = 0
        try:
            while self.running:
                cycle_count += 1
                print(f"\n📍 CYCLE #{cycle_count}")
                self.run_cycle()

                # Wait 5 minutes between cycles
                print(f"⏸️  Waiting 5 minutes until next cycle...")
                time.sleep(300)

        except KeyboardInterrupt:
            print("\n\n⏹️  Autonomous loop stopped by user")
            print(f"Completed {cycle_count} cycles")

            # Show final stats
            print("\n📊 FINAL STATISTICS:")
            api_stats = self.orchestrator.api_manager.get_api_stats()
            print(f"  Total API Calls: {api_stats['total_calls']}")
            print(f"  Success Rate: {api_stats['success_rate']:.1%}")
            print(f"  Total Cost: ${api_stats['total_cost']:.4f}")
            print(f"  Net Value: ${api_stats['net_value']:.2f}")


def main():
    """Run full autonomous system via APIs."""
    loop = AutonomousLoop()

    # Check if running in background mode
    if "--daemon" in sys.argv:
        # Run as background daemon
        loop.run_forever()
    else:
        # Run single cycle for testing
        loop.run_cycle()


if __name__ == "__main__":
    main()
