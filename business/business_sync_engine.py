#!/usr/bin/env python3
"""
Business Synchronization Engine
Keeps Yair Siegel's business state synchronized across all systems
Runs continuously to monitor and optimize business operations
"""
import json
import pathlib
import datetime
import time
import sys
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager

REPO_ROOT = pathlib.Path(__file__).parent.parent
SYNC_LOG = REPO_ROOT / "business/data/sync_log.jsonl"
SYNC_STATE = REPO_ROOT / "business/data/sync_state.json"


class BusinessSyncEngine:
    """Synchronizes business state across all systems"""

    def __init__(self):
        self.profile_manager = BusinessProfileManager()
        self.sync_log_path = SYNC_LOG
        self.sync_state_path = SYNC_STATE
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure required directories exist"""
        self.sync_log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_sync_event(self, event_type: str, details: Dict[str, Any]):
        """Log a synchronization event"""
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "details": details,
        }
        with open(self.sync_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def load_sync_state(self) -> Dict[str, Any]:
        """Load last synchronization state"""
        if self.sync_state_path.exists():
            return json.loads(self.sync_state_path.read_text())
        return {
            "last_sync": None,
            "sync_count": 0,
            "last_profile_hash": None,
        }

    def save_sync_state(self, state: Dict[str, Any]):
        """Save synchronization state"""
        self.sync_state_path.write_text(json.dumps(state, indent=2))

    def calculate_profile_hash(self, profile) -> str:
        """Calculate simple hash of profile for change detection"""
        # Use key financial values
        data = f"{profile.business_accounts.total_business_liquid}|{profile.personal_accounts.total_personal_liquid}|{profile.credit_profile.credit_utilization}|{profile.business_health.total_net_worth}"
        return str(hash(data))

    def detect_changes(self, old_profile, new_profile) -> List[Dict[str, Any]]:
        """Detect significant changes between profiles"""
        changes = []

        # Net worth changes
        old_nw = old_profile.business_health.total_net_worth
        new_nw = new_profile.business_health.total_net_worth
        if abs(new_nw - old_nw) > 10:  # $10+ change
            changes.append({
                "type": "net_worth_change",
                "old_value": old_nw,
                "new_value": new_nw,
                "delta": new_nw - old_nw,
                "delta_pct": ((new_nw - old_nw) / old_nw * 100) if old_nw != 0 else 0,
            })

        # Credit utilization changes
        old_util = old_profile.credit_profile.credit_utilization
        new_util = new_profile.credit_profile.credit_utilization
        if abs(new_util - old_util) > 0.05:  # 5%+ change
            changes.append({
                "type": "credit_utilization_change",
                "old_value": old_util,
                "new_value": new_util,
                "delta": new_util - old_util,
            })

        # Business health score changes
        old_score = old_profile.business_health.business_score
        new_score = new_profile.business_health.business_score
        if abs(new_score - old_score) > 5:  # 5+ point change
            changes.append({
                "type": "health_score_change",
                "old_value": old_score,
                "new_value": new_score,
                "delta": new_score - old_score,
            })

        # New improvement opportunities
        old_opps = set(old_profile.business_health.improvement_opportunities)
        new_opps = set(new_profile.business_health.improvement_opportunities)
        added_opps = new_opps - old_opps
        removed_opps = old_opps - new_opps

        if added_opps:
            changes.append({
                "type": "new_opportunities",
                "opportunities": list(added_opps),
            })

        if removed_opps:
            changes.append({
                "type": "resolved_opportunities",
                "opportunities": list(removed_opps),
            })

        return changes

    def sync_financial_data(self) -> Dict[str, Any]:
        """Synchronize financial data from all sources"""
        result = {
            "success": True,
            "sources_synced": [],
            "errors": [],
        }

        try:
            # Load external accounts
            ext_accounts = self.profile_manager.load_external_accounts()
            result["sources_synced"].append("external_accounts")
        except Exception as e:
            result["errors"].append(f"Failed to load external accounts: {e}")
            result["success"] = False

        try:
            # Load finance state
            fin_state = self.profile_manager.load_finance_state()
            result["sources_synced"].append("finance_state")
        except Exception as e:
            result["errors"].append(f"Failed to load finance state: {e}")

        try:
            # Load cards data
            cards = self.profile_manager.load_cards_data()
            result["sources_synced"].append("cards_data")
        except Exception as e:
            result["errors"].append(f"Failed to load cards data: {e}")

        return result

    def sync_business_metrics(self) -> Dict[str, Any]:
        """Synchronize business operation metrics"""
        result = {
            "success": True,
            "metrics_synced": [],
            "errors": [],
        }

        # TODO: Integrate with actual AI Nexus and trading system metrics
        # For now, mark as placeholder
        result["metrics_synced"].append("placeholder:ai_nexus_metrics")
        result["metrics_synced"].append("placeholder:trading_metrics")
        result["metrics_synced"].append("placeholder:automation_uptime")

        return result

    def perform_sync(self) -> Dict[str, Any]:
        """Perform complete synchronization cycle"""
        sync_start = datetime.datetime.utcnow()

        self.log_sync_event("sync_start", {})

        # Load previous sync state
        sync_state = self.load_sync_state()
        old_profile = None
        if sync_state["last_sync"]:
            try:
                old_profile = self.profile_manager.load_current_profile()
            except:
                pass

        # Sync financial data
        fin_sync = self.sync_financial_data()
        self.log_sync_event("financial_sync", fin_sync)

        # Sync business metrics
        metrics_sync = self.sync_business_metrics()
        self.log_sync_event("metrics_sync", metrics_sync)

        # Generate new profile
        new_profile = self.profile_manager.generate_current_profile()
        self.profile_manager.save_profile(new_profile)

        # Detect changes
        changes = []
        if old_profile:
            changes = self.detect_changes(old_profile, new_profile)
            if changes:
                self.log_sync_event("changes_detected", {"changes": changes})

        # Update sync state
        new_hash = self.calculate_profile_hash(new_profile)
        sync_state["last_sync"] = sync_start.isoformat() + "Z"
        sync_state["sync_count"] = sync_state.get("sync_count", 0) + 1
        sync_state["last_profile_hash"] = new_hash
        self.save_sync_state(sync_state)

        sync_duration = (datetime.datetime.utcnow() - sync_start).total_seconds()

        result = {
            "success": fin_sync["success"] and metrics_sync["success"],
            "timestamp": sync_start.isoformat() + "Z",
            "duration_seconds": sync_duration,
            "sources_synced": fin_sync["sources_synced"],
            "metrics_synced": metrics_sync["metrics_synced"],
            "changes_detected": len(changes),
            "changes": changes,
            "profile": {
                "net_worth": new_profile.business_health.total_net_worth,
                "health_score": new_profile.business_health.business_score,
                "credit_utilization": new_profile.credit_profile.credit_utilization,
                "improvement_opportunities": len(new_profile.business_health.improvement_opportunities),
            },
        }

        self.log_sync_event("sync_complete", result)

        return result

    def run_continuous(self, interval_seconds: int = 300):
        """Run synchronization continuously"""
        print(f"Business Sync Engine starting...")
        print(f"Sync interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")

        while True:
            try:
                print(f"\n[{datetime.datetime.utcnow().isoformat()}] Starting sync...")
                result = self.perform_sync()

                if result["success"]:
                    print(f"✓ Sync completed in {result['duration_seconds']:.2f}s")
                    print(f"  Net Worth: ${result['profile']['net_worth']:,.2f}")
                    print(f"  Health Score: {result['profile']['health_score']}/100")
                    print(f"  Credit Util: {result['profile']['credit_utilization']*100:.1f}%")
                    if result['changes_detected'] > 0:
                        print(f"  Changes detected: {result['changes_detected']}")
                else:
                    print(f"✗ Sync completed with errors")

            except Exception as e:
                print(f"✗ Sync error: {e}")
                self.log_sync_event("sync_error", {"error": str(e)})

            print(f"Next sync in {interval_seconds} seconds...")
            time.sleep(interval_seconds)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Business Synchronization Engine")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Sync interval in seconds (default: 300)")
    args = parser.parse_args()

    engine = BusinessSyncEngine()

    if args.once:
        print("Running single sync...")
        result = engine.perform_sync()
        print(json.dumps(result, indent=2))
    else:
        engine.run_continuous(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
