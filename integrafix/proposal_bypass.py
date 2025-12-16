#!/usr/bin/env python3
"""
INTEGRAFIX: Proposal Bypass System
===================================

Auto-sends low-risk, high-value proposals without human review.

BYPASS CRITERIA:
1. Value < $100 (low financial risk)
2. ABCFC score > 50 (positive expected value)
3. Source in whitelist (GitHub, known platforms)
4. No red flags (scam indicators, unrealistic terms)

Integration with income_engine:
- Checks each drafted proposal
- Auto-sends if bypass approved
- Queues for human review if not

Author: Claude + Yair
Created: 2025-12-16
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
BYPASS_CONFIG = STATE_DIR / "proposal_bypass_config.json"


class ProposalBypass:
    """
    Determines if proposals can be auto-sent without human review.

    INTEGRAFIX: Wires human bypass logic to income_engine proposals.
    """

    # Default bypass thresholds
    DEFAULT_MAX_VALUE = 100.0
    DEFAULT_MIN_ABCFC_SCORE = 50.0

    # Trusted sources (auto-approve)
    TRUSTED_SOURCES = {
        "github_bounties",
        "algora_bounties",
        "gitcoin",
        "direct_client_referral"
    }

    # Scam indicators (auto-reject)
    SCAM_KEYWORDS = [
        "crypto giveaway",
        "guaranteed profit",
        "pay upfront",
        "western union",
        "wire transfer first",
        "no contract",
        "cash only",
        "work from home scam"
    ]

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load bypass configuration."""
        if BYPASS_CONFIG.exists():
            with open(BYPASS_CONFIG) as f:
                return json.load(f)

        # Default config
        default = {
            "enabled": True,
            "max_value": self.DEFAULT_MAX_VALUE,
            "min_abcfc_score": self.DEFAULT_MIN_ABCFC_SCORE,
            "trusted_sources": list(self.TRUSTED_SOURCES),
            "custom_whitelist": [],  # Additional trusted sources
            "bypass_count": 0,
            "manual_review_count": 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        self._save_config(default)
        return default

    def _save_config(self, config: Optional[Dict] = None):
        """Save bypass configuration."""
        if config is None:
            config = self.config

        config["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(parents=True, exist_ok=True)

        with open(BYPASS_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)

    def should_bypass(self, proposal: Dict) -> Dict:
        """
        Determine if proposal should bypass human review.

        Returns:
            {
                "approved": bool,
                "reason": str,
                "checks": {
                    "value_ok": bool,
                    "score_ok": bool,
                    "source_ok": bool,
                    "no_red_flags": bool
                }
            }
        """
        if not self.config.get("enabled", True):
            return {
                "approved": False,
                "reason": "Bypass disabled in config",
                "checks": {}
            }

        # Get opportunity details
        opp_id = proposal.get("opportunity_id")
        if not opp_id:
            return {
                "approved": False,
                "reason": "No opportunity_id",
                "checks": {}
            }

        # Load opportunity from income_engine state
        income_state_file = STATE_DIR / "income_engine.json"
        if not income_state_file.exists():
            return {
                "approved": False,
                "reason": "Income engine state not found",
                "checks": {}
            }

        with open(income_state_file) as f:
            income_state = json.load(f)

        opportunity = income_state.get("opportunities", {}).get(opp_id)
        if not opportunity:
            return {
                "approved": False,
                "reason": f"Opportunity {opp_id} not found",
                "checks": {}
            }

        # Run bypass checks
        checks = {}

        # 1. Value check
        est_value = opportunity.get("est_value", 0)
        max_value = self.config.get("max_value", self.DEFAULT_MAX_VALUE)
        checks["value_ok"] = est_value <= max_value

        # 2. ABCFC score check
        abcfc_score = opportunity.get("abcfc_score", 0)
        min_score = self.config.get("min_abcfc_score", self.DEFAULT_MIN_ABCFC_SCORE)
        checks["score_ok"] = abcfc_score >= min_score

        # 3. Source check
        source = opportunity.get("source", "")
        trusted = set(self.config.get("trusted_sources", [])) | set(self.config.get("custom_whitelist", []))
        checks["source_ok"] = source in trusted

        # 4. Red flag check
        title = opportunity.get("title", "").lower()
        description = opportunity.get("description", "").lower()
        content = proposal.get("content", "").lower()

        has_red_flags = any(
            keyword in title or keyword in description or keyword in content
            for keyword in self.SCAM_KEYWORDS
        )
        checks["no_red_flags"] = not has_red_flags

        # Determine approval
        approved = all(checks.values())

        if approved:
            reason = "All bypass criteria met"
            self.config["bypass_count"] = self.config.get("bypass_count", 0) + 1
        else:
            failed_checks = [k for k, v in checks.items() if not v]
            reason = f"Failed checks: {', '.join(failed_checks)}"
            self.config["manual_review_count"] = self.config.get("manual_review_count", 0) + 1

        self._save_config()

        return {
            "approved": approved,
            "reason": reason,
            "checks": checks,
            "est_value": est_value,
            "abcfc_score": abcfc_score,
            "source": source
        }

    def get_stats(self) -> Dict:
        """Get bypass statistics."""
        return {
            "enabled": self.config.get("enabled", True),
            "bypass_count": self.config.get("bypass_count", 0),
            "manual_review_count": self.config.get("manual_review_count", 0),
            "bypass_rate": (
                self.config.get("bypass_count", 0) /
                max(1, self.config.get("bypass_count", 0) + self.config.get("manual_review_count", 0))
            ),
            "thresholds": {
                "max_value": self.config.get("max_value", self.DEFAULT_MAX_VALUE),
                "min_abcfc_score": self.config.get("min_abcfc_score", self.DEFAULT_MIN_ABCFC_SCORE)
            }
        }


# CLI interface
if __name__ == "__main__":
    import sys

    bypass = ProposalBypass()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "stats":
            stats = bypass.get_stats()
            print(json.dumps(stats, indent=2))

        elif cmd == "enable":
            bypass.config["enabled"] = True
            bypass._save_config()
            print("✓ Bypass enabled")

        elif cmd == "disable":
            bypass.config["enabled"] = False
            bypass._save_config()
            print("✓ Bypass disabled")

        elif cmd == "set-max-value" and len(sys.argv) > 2:
            bypass.config["max_value"] = float(sys.argv[2])
            bypass._save_config()
            print(f"✓ Max value set to ${bypass.config['max_value']}")

        elif cmd == "set-min-score" and len(sys.argv) > 2:
            bypass.config["min_abcfc_score"] = float(sys.argv[2])
            bypass._save_config()
            print(f"✓ Min ABCFC score set to {bypass.config['min_abcfc_score']}")

        else:
            print("Usage:")
            print("  python proposal_bypass.py stats")
            print("  python proposal_bypass.py enable|disable")
            print("  python proposal_bypass.py set-max-value <amount>")
            print("  python proposal_bypass.py set-min-score <score>")
    else:
        stats = bypass.get_stats()
        print(json.dumps(stats, indent=2))
