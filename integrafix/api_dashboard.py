#!/usr/bin/env python3
"""
API Management Dashboard
========================

Command center for the entire API-driven system.
View status, trigger operations, optimize ABCFC scores.

Master: Yair Siegel
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

from api_orchestrator import APIOrchestrator


class APIDashboard:
    """Management dashboard for API system."""

    def __init__(self):
        self.orchestrator = APIOrchestrator()

    def show_main_menu(self):
        """Display main menu."""
        print("\n" + "=" * 80)
        print("🎯 API SYSTEM DASHBOARD")
        print("=" * 80)
        print()
        print("VERTICALS:")
        print("  1. Money Printer (Trading)")
        print("  2. GitHub Bounty Hunter")
        print("  3. Bug Bounty Hunter")
        print()
        print("SYSTEM:")
        print("  4. Run Full Cycle")
        print("  5. View System Status")
        print("  6. View API Statistics")
        print("  7. Optimize ABCFC Scores")
        print()
        print("  0. Exit")
        print("=" * 80)

    def show_money_printer_menu(self):
        """Money Printer operations."""
        print("\n💰 MONEY PRINTER (V1)")
        print("-" * 80)
        print("  1. Get Active Markets")
        print("  2. Get Orderbook")
        print("  3. Place Order")
        print("  0. Back")

    def show_bounty_hunter_menu(self):
        """Bounty Hunter operations."""
        print("\n🎯 BOUNTY HUNTER (V2)")
        print("-" * 80)
        print("  1. Search Bounties")
        print("  2. Get Issue Details")
        print("  3. Claim Bounty")
        print("  4. Create Pull Request")
        print("  0. Back")

    def show_bug_bounty_menu(self):
        """Bug Bounty Hunter operations."""
        print("\n🔒 BUG BOUNTY HUNTER (V3)")
        print("-" * 80)
        print("  1. List Programs")
        print("  2. Submit Report")
        print("  0. Back")

    def run_full_cycle(self):
        """Run complete autonomous cycle."""
        print("\n🚀 Running full autonomous cycle...")
        results = self.orchestrator.run_full_cycle()
        print("\n✅ Cycle complete!")
        return results

    def show_system_status(self):
        """Display system status."""
        print("\n" + "=" * 80)
        print("📊 SYSTEM STATUS")
        print("=" * 80)

        status = self.orchestrator.get_system_status()

        print("\n🟢 VERTICALS:")
        print("-" * 80)
        for name, data in status["orchestrator"]["verticals"].items():
            status_icon = "✅" if data["status"] == "active" else "⏸️"
            print(f"  {status_icon} {name.replace('_', ' ').title()}")
            print(f"     Operations: {data['operations']}")
        print()

        print("📊 METRICS:")
        print("-" * 80)
        print(f"  Total Operations: {status['orchestrator']['total_operations']}")
        print(f"  Total Value: ${status['orchestrator']['total_value_generated']:.2f}")
        print()

        print("💰 API ECONOMICS:")
        print("-" * 80)
        api = status["api_manager"]
        print(f"  API Calls: {api['total_calls']}")
        print(f"  Success Rate: {api['success_rate']:.1%}")
        print(f"  Cost: ${api['total_cost']:.4f}")
        print(f"  Net Value: ${api['net_value']:.2f}")
        if api['roi'] != float('inf'):
            print(f"  ROI: {api['roi']:.1f}x")
        else:
            print(f"  ROI: ∞ (zero cost)")
        print()

    def show_api_stats(self):
        """Display detailed API statistics."""
        print("\n" + "=" * 80)
        print("📈 API STATISTICS")
        print("=" * 80)

        registry = self.orchestrator.api_manager.registry

        print("\n🏆 TOP 10 APIS (by ABCFC Score):")
        print("-" * 80)
        top_apis = registry.get_best_apis(limit=10)
        for i, api in enumerate(top_apis, 1):
            print(f"\n  {i}. {api['name']}")
            print(f"     Category: {api['category']}, Provider: {api['provider']}")
            print(f"     ABCFC Score: {api['abcfc_score']:.2f}")
            print(f"     Cost: ${api['cost_per_call']:.4f}")
            print(f"     Expected Value: ${api['expected_value']:.2f}")
            print(f"     Success Probability: {api['success_probability']:.1%}")

        print()

    def optimize_abcfc(self):
        """Show ABCFC optimization recommendations."""
        print("\n" + "=" * 80)
        print("🎯 ABCFC OPTIMIZATION")
        print("=" * 80)

        registry = self.orchestrator.api_manager.registry

        print("\n💡 RECOMMENDATIONS:")
        print("-" * 80)

        # Get top APIs by category
        categories = ["trading", "github", "security", "infrastructure"]
        for category in categories:
            print(f"\n📊 {category.upper()}:")
            best = registry.get_best_apis(category=category, limit=3)
            for i, api in enumerate(best, 1):
                print(f"  {i}. Use '{api['name']}' (Score: {api['abcfc_score']:.2f})")

        print()

    def search_bounties(self):
        """Search for GitHub bounties."""
        print("\n🔍 Searching for bounties...")
        result = self.orchestrator.search_github_bounties()

        if result.success:
            bounties = result.data.get("parsed_bounties", [])
            print(f"\n✅ Found {len(bounties)} bounties")
            print(f"Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")
            print(f"ABCFC Score: {result.abcfc_score:.2f}")

            if bounties:
                print("\nTop 5 bounties:")
                for i, bounty in enumerate(bounties[:5], 1):
                    repo_str = "/".join(bounty["repo"])
                    print(f"\n  {i}. {bounty['title']}")
                    print(f"     Repo: {repo_str}")
                    print(f"     Issue: #{bounty['issue_number']}")
                    if bounty['amount'] > 0:
                        print(f"     Amount: ${bounty['amount']:.2f}")
                    print(f"     URL: {bounty['url']}")
        else:
            print(f"❌ Failed: {result.error}")

    def get_markets(self):
        """Get Polymarket markets."""
        print("\n🔍 Getting active markets...")
        result = self.orchestrator.get_polymarket_markets()

        if result.success:
            markets = result.data
            print(f"\n✅ Found {len(markets)} markets")
            print(f"Cost: ${result.cost:.4f}, Duration: {result.duration:.2f}s")
            print(f"ABCFC Score: {result.abcfc_score:.2f}")

            if markets:
                print("\nRecent markets:")
                for i, market in enumerate(markets[:5], 1):
                    print(f"\n  {i}. {market.get('question', 'Unknown')}")
                    print(f"     Tokens: {market.get('tokens', [])}")
        else:
            print(f"❌ Failed: {result.error}")

    def interactive_mode(self):
        """Run interactive dashboard."""
        while True:
            self.show_main_menu()
            choice = input("\nSelect option: ").strip()

            if choice == "0":
                print("\n👋 Goodbye!")
                break

            elif choice == "1":
                # Money Printer submenu
                while True:
                    self.show_money_printer_menu()
                    sub_choice = input("\nSelect option: ").strip()
                    if sub_choice == "0":
                        break
                    elif sub_choice == "1":
                        self.get_markets()
                        input("\nPress Enter to continue...")
                    elif sub_choice == "2":
                        token_id = input("Enter token ID: ").strip()
                        if token_id:
                            result = self.orchestrator.get_orderbook(token_id)
                            if result.success:
                                print(f"\n✅ Orderbook retrieved")
                                print(f"Bids: {len(result.data.get('bids', []))}")
                                print(f"Asks: {len(result.data.get('asks', []))}")
                            else:
                                print(f"❌ {result.error}")
                        input("\nPress Enter to continue...")

            elif choice == "2":
                # Bounty Hunter submenu
                while True:
                    self.show_bounty_hunter_menu()
                    sub_choice = input("\nSelect option: ").strip()
                    if sub_choice == "0":
                        break
                    elif sub_choice == "1":
                        self.search_bounties()
                        input("\nPress Enter to continue...")

            elif choice == "3":
                # Bug Bounty Hunter submenu
                while True:
                    self.show_bug_bounty_menu()
                    sub_choice = input("\nSelect option: ").strip()
                    if sub_choice == "0":
                        break
                    elif sub_choice == "1":
                        result = self.orchestrator.list_bug_bounty_programs()
                        if result.success:
                            print(f"\n✅ Programs retrieved")
                        else:
                            print(f"❌ {result.error}")
                        input("\nPress Enter to continue...")

            elif choice == "4":
                self.run_full_cycle()
                input("\nPress Enter to continue...")

            elif choice == "5":
                self.show_system_status()
                input("\nPress Enter to continue...")

            elif choice == "6":
                self.show_api_stats()
                input("\nPress Enter to continue...")

            elif choice == "7":
                self.optimize_abcfc()
                input("\nPress Enter to continue...")

            else:
                print("\n❌ Invalid option")
                input("Press Enter to continue...")


def main():
    """Run dashboard."""
    dashboard = APIDashboard()

    # Check if running in interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        dashboard.interactive_mode()
    else:
        # Default: show status and run cycle
        print("🚀 API SYSTEM DASHBOARD")
        print("=" * 80)
        print()

        dashboard.show_system_status()
        print("\n" + "=" * 80)

        # Run full cycle
        dashboard.run_full_cycle()

        print("\n💡 Tip: Run with --interactive for interactive mode")
        print()


if __name__ == "__main__":
    main()
