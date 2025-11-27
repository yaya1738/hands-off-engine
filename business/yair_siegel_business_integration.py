#!/usr/bin/env python3
"""
Yair Siegel Business Integration
Master integration that connects all business systems together
Combines: Business Profile + Sync Engine + Optimization Agent + AI Nexus
"""
import json
import pathlib
import datetime
import sys
import time
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager
from business.business_sync_engine import BusinessSyncEngine
from business.business_optimization_agent import BusinessOptimizationAgent

REPO_ROOT = pathlib.Path(__file__).parent.parent
INTEGRATION_LOG = REPO_ROOT / "business/data/integration_log.jsonl"
INTEGRATION_STATE = REPO_ROOT / "business/data/integration_state.json"


class YairSiegelBusinessIntegration:
    """Master integration for Yair Siegel's business systems"""

    def __init__(self):
        self.profile_manager = BusinessProfileManager()
        self.sync_engine = BusinessSyncEngine()
        self.optimization_agent = BusinessOptimizationAgent()
        self.integration_log_path = INTEGRATION_LOG
        self.integration_state_path = INTEGRATION_STATE
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure required directories exist"""
        self.integration_log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Log an integration event"""
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "details": details,
        }
        with open(self.integration_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load_integration_state(self) -> Dict[str, Any]:
        """Load integration state"""
        if self.integration_state_path.exists():
            return json.loads(self.integration_state_path.read_text())
        return {
            "initialized": False,
            "last_full_cycle": None,
            "cycles_completed": 0,
        }

    def save_integration_state(self, state: Dict[str, Any]):
        """Save integration state"""
        self.integration_state_path.write_text(json.dumps(state, indent=2))

    def initialize_business_systems(self) -> Dict[str, Any]:
        """Initialize all business systems"""
        self.log_event("initialization_start", {})

        result = {
            "success": True,
            "components_initialized": [],
            "errors": [],
        }

        try:
            # Initialize business profile
            profile = self.profile_manager.generate_current_profile()
            self.profile_manager.save_profile(profile)
            result["components_initialized"].append("business_profile")
            self.log_event("business_profile_initialized", {
                "health_score": profile.business_health.business_score,
                "net_worth": profile.business_health.total_net_worth,
            })
        except Exception as e:
            result["errors"].append(f"Business profile init failed: {e}")
            result["success"] = False

        try:
            # Run initial sync
            sync_result = self.sync_engine.perform_sync()
            result["components_initialized"].append("sync_engine")
            self.log_event("sync_engine_initialized", sync_result)
        except Exception as e:
            result["errors"].append(f"Sync engine init failed: {e}")

        try:
            # Run initial optimization analysis
            opt_result = self.optimization_agent.run_optimization_cycle()
            result["components_initialized"].append("optimization_agent")
            self.log_event("optimization_agent_initialized", {
                "recommendations": opt_result["recommendations_count"],
            })
        except Exception as e:
            result["errors"].append(f"Optimization agent init failed: {e}")

        # Update integration state
        state = self.load_integration_state()
        state["initialized"] = result["success"]
        state["initialization_time"] = datetime.datetime.utcnow().isoformat() + "Z"
        self.save_integration_state(state)

        self.log_event("initialization_complete", result)

        return result

    def run_full_business_cycle(self) -> Dict[str, Any]:
        """Run complete business cycle: Sync -> Profile -> Optimize"""
        cycle_start = datetime.datetime.utcnow()

        self.log_event("business_cycle_start", {})

        result = {
            "timestamp": cycle_start.isoformat() + "Z",
            "success": True,
            "steps": {},
        }

        # Step 1: Synchronize data
        try:
            sync_result = self.sync_engine.perform_sync()
            result["steps"]["sync"] = {
                "success": sync_result["success"],
                "duration": sync_result["duration_seconds"],
                "changes": sync_result["changes_detected"],
            }
        except Exception as e:
            result["steps"]["sync"] = {"success": False, "error": str(e)}
            result["success"] = False

        # Step 2: Generate current profile
        try:
            profile = self.profile_manager.generate_current_profile()
            result["steps"]["profile"] = {
                "success": True,
                "health_score": profile.business_health.business_score,
                "net_worth": profile.business_health.total_net_worth,
                "credit_utilization": profile.credit_profile.credit_utilization,
            }
        except Exception as e:
            result["steps"]["profile"] = {"success": False, "error": str(e)}
            result["success"] = False

        # Step 3: Run optimization analysis
        try:
            opt_result = self.optimization_agent.run_optimization_cycle()
            result["steps"]["optimization"] = {
                "success": True,
                "recommendations": opt_result["recommendations_count"],
            }
        except Exception as e:
            result["steps"]["optimization"] = {"success": False, "error": str(e)}

        # Calculate cycle duration
        cycle_duration = (datetime.datetime.utcnow() - cycle_start).total_seconds()
        result["duration_seconds"] = cycle_duration

        # Update integration state
        state = self.load_integration_state()
        state["last_full_cycle"] = result["timestamp"]
        state["cycles_completed"] = state.get("cycles_completed", 0) + 1
        self.save_integration_state(state)

        self.log_event("business_cycle_complete", result)

        return result

    def get_business_dashboard(self) -> str:
        """Generate comprehensive business dashboard"""
        profile = self.profile_manager.generate_current_profile()
        opt_result = self.optimization_agent.run_optimization_cycle()

        lines = [
            "=" * 80,
            "YAIR SIEGEL BUSINESS DASHBOARD",
            "=" * 80,
            f"Generated: {datetime.datetime.utcnow().isoformat()}Z",
            "",
            "BUSINESS HEALTH OVERVIEW:",
            f"  Overall Score:          {profile.business_health.business_score}/100",
            f"  Total Net Worth:        ${profile.business_health.total_net_worth:,.2f}",
            f"  Credit Utilization:     {profile.credit_profile.credit_utilization*100:.1f}%",
            f"  Credit Score:           {profile.credit_profile.credit_score}",
            "",
            "LIQUIDITY POSITION:",
            f"  Business Liquid:        ${profile.business_accounts.total_business_liquid:,.2f}",
            f"  Personal Liquid:        ${profile.personal_accounts.total_personal_liquid:,.2f}",
            f"  Total Liquid:           ${profile.business_accounts.total_business_liquid + profile.personal_accounts.total_personal_liquid:,.2f}",
            "",
            "BUSINESS ACCOUNTS:",
            f"  PayPal Business:        ${profile.business_accounts.paypal_business:,.2f}",
            f"  PayPal Cashback:        ${profile.business_accounts.paypal_cashback_balance:,.2f}",
            "",
            "SYSTEM OPERATIONS:",
            f"  Trading System:         {'Active' if profile.business_operations.trading_system_active else 'Inactive'}",
            f"  AI Nexus:               {'Active' if profile.business_operations.ai_nexus_active else 'Inactive'}",
            f"  Automation Uptime:      {profile.business_operations.automation_uptime_pct:.1f}%",
            "",
            f"TOP OPTIMIZATION OPPORTUNITIES ({len(opt_result['recommendations'])}):",
            "",
        ]

        # Show top 5 recommendations
        top_recommendations = opt_result['recommendations'][:5]
        if top_recommendations:
            for i, rec in enumerate(top_recommendations, 1):
                lines.append(f"{i}. [{rec['priority']}] {rec['description']}")
                lines.append(f"   Expected Impact: {rec['expected_impact']}")
                lines.append("")
        else:
            lines.append("No critical opportunities - business is operating optimally!")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def run_continuous(self, cycle_interval_seconds: int = 3600):
        """Run continuous business integration"""
        print(f"Yair Siegel Business Integration starting...")
        print(f"Cycle interval: {cycle_interval_seconds} seconds ({cycle_interval_seconds/3600:.1f} hours)")

        # Initialize on first run
        state = self.load_integration_state()
        if not state.get("initialized"):
            print("\nInitializing business systems...")
            init_result = self.initialize_business_systems()
            if init_result["success"]:
                print("✓ Initialization complete")
            else:
                print("✗ Initialization had errors:")
                for error in init_result["errors"]:
                    print(f"  - {error}")

        while True:
            try:
                print(f"\n[{datetime.datetime.utcnow().isoformat()}] Running business cycle...")
                result = self.run_full_business_cycle()

                if result["success"]:
                    print(f"✓ Cycle completed in {result['duration_seconds']:.2f}s")
                    if "profile" in result["steps"]:
                        print(f"  Health Score: {result['steps']['profile']['health_score']}/100")
                        print(f"  Net Worth: ${result['steps']['profile']['net_worth']:,.2f}")
                    if "optimization" in result["steps"]:
                        print(f"  Recommendations: {result['steps']['optimization']['recommendations']}")
                else:
                    print(f"✗ Cycle had errors")

            except Exception as e:
                print(f"✗ Cycle error: {e}")
                self.log_event("cycle_error", {"error": str(e)})

            print(f"Next cycle in {cycle_interval_seconds} seconds...")
            time.sleep(cycle_interval_seconds)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Yair Siegel Business Integration")
    parser.add_argument("--init", action="store_true", help="Initialize business systems")
    parser.add_argument("--cycle", action="store_true", help="Run single business cycle")
    parser.add_argument("--dashboard", action="store_true", help="Show business dashboard")
    parser.add_argument("--continuous", action="store_true", help="Run continuous integration")
    parser.add_argument("--interval", type=int, default=3600, help="Cycle interval in seconds (default: 3600)")
    args = parser.parse_args()

    integration = YairSiegelBusinessIntegration()

    if args.init:
        print("Initializing business systems...")
        result = integration.initialize_business_systems()
        print(json.dumps(result, indent=2))

    elif args.cycle:
        print("Running business cycle...")
        result = integration.run_full_business_cycle()
        print(json.dumps(result, indent=2))

    elif args.dashboard:
        print(integration.get_business_dashboard())

    elif args.continuous:
        integration.run_continuous(cycle_interval_seconds=args.interval)

    else:
        # Default: show dashboard
        print(integration.get_business_dashboard())


if __name__ == "__main__":
    main()
