#!/usr/bin/env python3
"""
Enhanced Autonomous Loop - Maximum Capability Execution
Runs all available autonomous systems at full power.

Serving: Yair Siegel
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
sys.path.insert(0, str(PROJECT_ROOT))

MASTER = "Yair Siegel"
LOOP_STATE = STATE_DIR / "enhanced_loop_state.json"


class EnhancedLoop:
    """Maximum capability autonomous execution."""

    def __init__(self):
        self.state = self._load_state()
        self.results = {}

    def _load_state(self) -> Dict:
        if LOOP_STATE.exists():
            with open(LOOP_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_cycles": 0,
            "actions_taken": 0,
            "income_generated": 0.0,
            "capabilities_used": []
        }

    def _save_state(self):
        self.state["last_run"] = datetime.now(timezone.utc).isoformat()
        with open(LOOP_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def run_all_systems(self) -> Dict:
        """Run all autonomous systems at maximum capability."""
        print("=" * 70)
        print("ENHANCED AUTONOMOUS LOOP - MAXIMUM CAPABILITY")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "systems_run": [],
            "actions_taken": 0,
            "errors": []
        }

        # 1. Reality Check
        print("[1/7] REALITY CHECK")
        try:
            from autonomous.reality_feedback import RealityFeedback
            rf = RealityFeedback()
            reality = rf.reality_check()
            results["reality"] = {
                "signals": len(reality.get("signals", [])),
                "effective_actions": len(reality.get("analysis", {}).get("effective", [])),
                "ineffective_actions": len(reality.get("analysis", {}).get("ineffective", []))
            }
            results["systems_run"].append("reality_feedback")
            print(f"  ✓ Signals: {results['reality']['signals']}")
        except Exception as e:
            results["errors"].append(f"reality_feedback: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # 2. Conversion Optimizer
        print("[2/7] CONVERSION OPTIMIZER")
        try:
            from autonomous.conversion_optimizer import ConversionOptimizer
            co = ConversionOptimizer()
            conversion = co.adapt_now()
            results["conversion"] = {
                "experiment_id": conversion.get("experiment", {}).get("id"),
                "testing": conversion.get("experiment", {}).get("lever"),
                "issues_found": len(conversion.get("diagnosis", {}).get("likely_issues", []))
            }
            results["systems_run"].append("conversion_optimizer")
            print(f"  ✓ Testing: {results['conversion']['testing']}")
        except Exception as e:
            results["errors"].append(f"conversion_optimizer: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # 3. Active Pursuit
        print("[3/7] ACTIVE PURSUIT")
        try:
            from autonomous.active_pursuit import ActivePursuit
            ap = ActivePursuit()
            pursuit = ap.pursue_actively()
            results["pursuit"] = {
                "freelance_opportunities": len(pursuit.get("freelance", [])),
                "outreach_targets": len(pursuit.get("outreach", {}).get("targets", []))
            }
            results["systems_run"].append("active_pursuit")
            results["actions_taken"] += results["pursuit"]["freelance_opportunities"]
            print(f"  ✓ Opportunities: {results['pursuit']['freelance_opportunities']}")
        except Exception as e:
            results["errors"].append(f"active_pursuit: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # 4. Web Executor (NEW)
        print("[4/7] WEB EXECUTOR")
        try:
            from autonomous.web_executor import WebExecutor
            we = WebExecutor()

            # Scan GitHub
            github = we.execute_github_contribution()
            results["github"] = {
                "opportunities": len(github.get("actions", [])),
                "errors": len(github.get("errors", []))
            }

            # Generate content
            content = we.generate_content_for_platforms()
            results["content"] = {
                "posts_generated": len(content.get("posts", []))
            }

            # Scan freelance
            freelance = we.scan_freelance_platforms()
            results["freelance"] = {
                "skill_matches": len(freelance.get("opportunities", []))
            }

            results["systems_run"].append("web_executor")
            results["actions_taken"] += results["github"]["opportunities"]
            print(f"  ✓ GitHub opps: {results['github']['opportunities']}")
            print(f"  ✓ Content generated: {results['content']['posts_generated']}")
            print(f"  ✓ Freelance skills: {results['freelance']['skill_matches']}")
        except Exception as e:
            results["errors"].append(f"web_executor: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # 5. Self-Healer
        print("[5/7] SELF-HEALER")
        try:
            from autonomous.self_healer import SelfHealer
            sh = SelfHealer()
            health = sh.diagnose_and_heal()
            results["health"] = {
                "issues_found": health.get("issues_found", 0),
                "issues_fixed": health.get("issues_fixed", 0)
            }
            results["systems_run"].append("self_healer")
            print(f"  ✓ Fixed: {results['health']['issues_fixed']}/{results['health']['issues_found']}")
        except Exception as e:
            results["errors"].append(f"self_healer: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # 6. Self-Modification Check
        print("[6/7] SELF-MODIFICATION CHECK")
        try:
            from autonomous.self_modification import SelfModificationEngine
            sme = SelfModificationEngine()
            capability = sme.verify_self_modification_capability()
            results["self_mod"] = {
                "capability_score": capability.get("capability_score", 0),
                "fully_capable": capability.get("fully_capable", False)
            }
            results["systems_run"].append("self_modification")
            print(f"  ✓ Capability: {results['self_mod']['capability_score']}%")
        except Exception as e:
            results["errors"].append(f"self_modification: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # 7. Infrastructure Manager
        print("[7/7] INFRASTRUCTURE CHECK")
        try:
            # Check cron jobs
            cron_result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=5
            )
            cron_count = len([l for l in cron_result.stdout.split('\n') if l.strip() and not l.startswith('#')])

            # Check running processes
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=5
            )
            python_procs = len([l for l in ps_result.stdout.split('\n') if 'python' in l.lower()])

            results["infrastructure"] = {
                "cron_jobs": cron_count,
                "python_processes": python_procs
            }
            results["systems_run"].append("infrastructure")
            print(f"  ✓ Cron jobs: {cron_count}")
            print(f"  ✓ Python processes: {python_procs}")
        except Exception as e:
            results["errors"].append(f"infrastructure: {str(e)}")
            print(f"  ✗ Error: {e}")
        print()

        # Summary
        print("=" * 70)
        print("CYCLE COMPLETE")
        print("=" * 70)
        print(f"  Systems run: {len(results['systems_run'])}/7")
        print(f"  Actions taken: {results['actions_taken']}")
        print(f"  Errors: {len(results['errors'])}")
        print()

        # Update state
        self.state["total_cycles"] += 1
        self.state["actions_taken"] += results["actions_taken"]
        self.state["capabilities_used"] = list(set(
            self.state.get("capabilities_used", []) + results["systems_run"]
        ))
        self._save_state()

        return results

    def get_capability_summary(self) -> Dict:
        """Get summary of all available capabilities."""
        capabilities = {
            "autonomous_systems": [
                {"name": "reality_feedback", "purpose": "Track external reality vs internal metrics"},
                {"name": "conversion_optimizer", "purpose": "A/B test and optimize conversions"},
                {"name": "active_pursuit", "purpose": "Hunt income opportunities"},
                {"name": "web_executor", "purpose": "Execute web actions (Reddit, GitHub, content)"},
                {"name": "self_healer", "purpose": "Fix system issues automatically"},
                {"name": "self_modification", "purpose": "Improve own code"},
                {"name": "moonshot_loop", "purpose": "10x improvement attempts"}
            ],
            "income_paths": [
                {"path": "freelance", "platforms": ["Upwork", "Fiverr", "Toptal"], "estimated": "$200-2000/gig"},
                {"path": "trading", "status": "DRYRUN", "positions": "$98 pending"},
                {"path": "content", "platforms": ["LinkedIn", "Twitter", "Reddit"], "estimated": "Lead generation"},
                {"path": "github", "action": "Contribute to projects", "estimated": "Reputation + referrals"}
            ],
            "missing_for_full_autonomy": [
                "Reddit API credentials",
                "Twitter API credentials",
                "Upwork account (requires human)",
                "Fiverr account (requires human)",
                "Live trading enabled"
            ]
        }
        return capabilities


def main():
    """Run enhanced loop."""
    loop = EnhancedLoop()

    # Show capabilities
    print("\n[AVAILABLE CAPABILITIES]")
    caps = loop.get_capability_summary()
    for sys in caps["autonomous_systems"]:
        print(f"  • {sys['name']}: {sys['purpose']}")
    print()

    # Run all systems
    results = loop.run_all_systems()

    # Show what's needed for full autonomy
    print("\n[NEEDED FOR FULL AUTONOMY]")
    for item in caps["missing_for_full_autonomy"]:
        print(f"  ⚠ {item}")

    return results


if __name__ == "__main__":
    main()
