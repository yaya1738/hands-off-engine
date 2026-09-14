#!/usr/bin/env python3
"""
COST TRACKER - Track Every System Action and Its Cost
======================================================

Every action the system takes has a cost. This module:
1. Logs all billable actions with their costs
2. Tracks running totals by partner
3. Alerts on spending thresholds
4. Provides cost reports

CRITICAL RULES:
- DigitalOcean: Hourly billing, DESTROYED = only way to stop charges
- OpenAI: Prepaid credits, fails when empty
- Anthropic: Per-token billing
- Groq/Google: Free but rate-limited
- Polymarket: USDC locked in positions

Serving: Yair Siegel
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

BASE_DIR = Path(__file__).parent.parent
FINANCE_DIR = BASE_DIR / 'finance'
FINANCE_DIR.mkdir(parents=True, exist_ok=True)

COST_LOG = FINANCE_DIR / 'cost_log.jsonl'
TERMS_FILE = FINANCE_DIR / 'partner_terms.json'
STATE_FILE = FINANCE_DIR / 'cost_state.json'

MASTER = "Yair Siegel"


@dataclass
class CostEntry:
    """Single cost entry."""
    timestamp: str
    partner: str
    action: str
    resource: str
    quantity: float
    unit: str
    unit_cost: float
    total_cost: float
    notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class CostState:
    """Running cost state."""
    total_today: float = 0.0
    total_this_month: float = 0.0
    by_partner: Dict[str, float] = field(default_factory=dict)
    by_partner_today: Dict[str, float] = field(default_factory=dict)
    last_updated: str = ""
    entries_today: int = 0
    alerts: List[str] = field(default_factory=list)


class CostTracker:
    """
    Track all system costs in real-time.

    Usage:
        tracker = CostTracker()
        tracker.log_cost("digitalocean", "droplet_hour", "ho-scale", 1, "hour", 0.14286)
        tracker.log_cost("openai", "api_call", "gpt-4-turbo", 1500, "tokens", 0.00001)
    """

    def __init__(self):
        self.terms = self._load_terms()
        self.state = self._load_state()
        self._reset_if_new_day()

    def _load_terms(self) -> Dict:
        """Load partner terms."""
        if TERMS_FILE.exists():
            with open(TERMS_FILE) as f:
                return json.load(f)
        return {"partners": {}}

    def _load_state(self) -> CostState:
        """Load cost state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    return CostState(**json.load(f))
            except:
                pass
        return CostState()

    def _save_state(self):
        """Save cost state."""
        self.state.last_updated = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)

    def _reset_if_new_day(self):
        """Reset daily counters if new day."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.state.last_updated:
            last_day = self.state.last_updated[:10]
            if last_day != today:
                self.state.total_today = 0.0
                self.state.by_partner_today = {}
                self.state.entries_today = 0
                self.state.alerts = []

    def log_cost(
        self,
        partner: str,
        action: str,
        resource: str,
        quantity: float,
        unit: str,
        unit_cost: float,
        notes: str = ""
    ) -> CostEntry:
        """
        Log a cost entry.

        Args:
            partner: Partner name (digitalocean, openai, etc.)
            action: Action type (droplet_hour, api_call, etc.)
            resource: Specific resource (droplet name, model name)
            quantity: Amount (hours, tokens, etc.)
            unit: Unit of quantity (hour, token, request)
            unit_cost: Cost per unit
            notes: Optional notes

        Returns:
            CostEntry object
        """
        total = quantity * unit_cost

        entry = CostEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            partner=partner,
            action=action,
            resource=resource,
            quantity=quantity,
            unit=unit,
            unit_cost=unit_cost,
            total_cost=total,
            notes=notes
        )

        # Update state
        self.state.total_today += total
        self.state.total_this_month += total
        self.state.entries_today += 1

        if partner not in self.state.by_partner:
            self.state.by_partner[partner] = 0.0
        self.state.by_partner[partner] += total

        if partner not in self.state.by_partner_today:
            self.state.by_partner_today[partner] = 0.0
        self.state.by_partner_today[partner] += total

        # Log to file
        with open(COST_LOG, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')

        # Check alerts
        self._check_alerts()

        self._save_state()
        return entry

    def _check_alerts(self):
        """Check for spending alerts."""
        config = self.terms.get("cost_tracking", {})
        daily_threshold = config.get("alert_threshold_daily", 10)
        monthly_threshold = config.get("alert_threshold_monthly", 200)

        if self.state.total_today > daily_threshold:
            alert = f"DAILY SPEND ALERT: ${self.state.total_today:.2f} exceeds ${daily_threshold}"
            if alert not in self.state.alerts:
                self.state.alerts.append(alert)
                print(f"[COST ALERT] {alert}")

        if self.state.total_this_month > monthly_threshold:
            alert = f"MONTHLY SPEND ALERT: ${self.state.total_this_month:.2f} exceeds ${monthly_threshold}"
            if alert not in self.state.alerts:
                self.state.alerts.append(alert)
                print(f"[COST ALERT] {alert}")

    def log_droplet_cost(self, droplet_name: str, size: str, hours: float = 1.0):
        """Convenience: Log DigitalOcean droplet cost."""
        pricing = self.terms.get("partners", {}).get("digitalocean", {}).get("pricing", {})
        hourly = pricing.get(size, {}).get("hourly", 0.14286)

        return self.log_cost(
            partner="digitalocean",
            action="droplet_hour",
            resource=droplet_name,
            quantity=hours,
            unit="hour",
            unit_cost=hourly,
            notes=f"Size: {size}"
        )

    def log_ai_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        """Convenience: Log AI API cost."""
        pricing = self.terms.get("partners", {}).get(provider, {}).get("pricing", {})
        model_pricing = pricing.get(model, {})

        input_cost = model_pricing.get("input_per_1k", 0) * (input_tokens / 1000)
        output_cost = model_pricing.get("output_per_1k", 0) * (output_tokens / 1000)
        total = input_cost + output_cost

        return self.log_cost(
            partner=provider,
            action="api_call",
            resource=model,
            quantity=input_tokens + output_tokens,
            unit="tokens",
            unit_cost=total / max(input_tokens + output_tokens, 1),
            notes=f"In: {input_tokens}, Out: {output_tokens}"
        )

    def estimate_droplet_cost(self, size: str, hours: float) -> float:
        """Estimate cost before creating droplet."""
        pricing = self.terms.get("partners", {}).get("digitalocean", {}).get("pricing", {})
        hourly = pricing.get(size, {}).get("hourly", 0.14286)
        return hourly * hours

    def get_current_droplet_hourly_burn(self) -> float:
        """Calculate current hourly burn rate from running droplets."""
        try:
            import subprocess
            result = subprocess.run(
                ["doctl", "compute", "droplet", "list", "--format", "Name,Memory,VCPUs", "--no-header"],
                capture_output=True, text=True
            )

            total_hourly = 0.0
            pricing = self.terms.get("partners", {}).get("digitalocean", {}).get("pricing", {})

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 3:
                        memory = int(parts[1])
                        vcpus = int(parts[2])

                        # Map to size
                        if vcpus == 4 and memory == 8192:
                            size = "s-4vcpu-8gb"
                        elif vcpus == 8 and memory == 16384:
                            size = "s-8vcpu-16gb-amd"
                        else:
                            size = "s-8vcpu-16gb-amd"

                        hourly = pricing.get(size, {}).get("hourly", 0.14286)
                        total_hourly += hourly

            return total_hourly
        except:
            return 0.0

    def get_summary(self) -> Dict:
        """Get cost summary."""
        hourly_burn = self.get_current_droplet_hourly_burn()

        return {
            "master": MASTER,
            "today": {
                "total": round(self.state.total_today, 2),
                "entries": self.state.entries_today,
                "by_partner": {k: round(v, 2) for k, v in self.state.by_partner_today.items()}
            },
            "this_month": {
                "total": round(self.state.total_this_month, 2),
                "by_partner": {k: round(v, 2) for k, v in self.state.by_partner.items()}
            },
            "current_burn": {
                "hourly": round(hourly_burn, 4),
                "daily": round(hourly_burn * 24, 2),
                "monthly": round(hourly_burn * 24 * 30, 2)
            },
            "alerts": self.state.alerts,
            "last_updated": self.state.last_updated
        }

    def get_partner_rules(self, partner: str) -> List[str]:
        """Get critical rules for a partner."""
        return self.terms.get("partners", {}).get(partner, {}).get("critical_rules", [])

    def print_report(self):
        """Print cost report."""
        summary = self.get_summary()

        print(f"\n{'='*50}")
        print(f"COST REPORT for {MASTER}")
        print(f"{'='*50}")

        print(f"\nTODAY:")
        print(f"  Total: ${summary['today']['total']:.2f}")
        print(f"  Entries: {summary['today']['entries']}")
        for partner, cost in summary['today']['by_partner'].items():
            print(f"    {partner}: ${cost:.2f}")

        print(f"\nTHIS MONTH:")
        print(f"  Total: ${summary['this_month']['total']:.2f}")
        for partner, cost in summary['this_month']['by_partner'].items():
            print(f"    {partner}: ${cost:.2f}")

        print(f"\nCURRENT BURN RATE:")
        print(f"  Hourly: ${summary['current_burn']['hourly']:.4f}")
        print(f"  Daily: ${summary['current_burn']['daily']:.2f}")
        print(f"  Monthly: ${summary['current_burn']['monthly']:.2f}")

        if summary['alerts']:
            print(f"\nALERTS:")
            for alert in summary['alerts']:
                print(f"  - {alert}")

        print(f"\n{'='*50}")


# Global instance
_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Cost Tracker")
    parser.add_argument("command", choices=["report", "log", "rules", "burn"])
    parser.add_argument("--partner", help="Partner name")
    parser.add_argument("--action", help="Action type")
    parser.add_argument("--resource", help="Resource name")
    parser.add_argument("--quantity", type=float, help="Quantity")
    parser.add_argument("--unit", help="Unit")
    parser.add_argument("--cost", type=float, help="Unit cost")

    args = parser.parse_args()
    tracker = get_cost_tracker()

    if args.command == "report":
        tracker.print_report()

    elif args.command == "burn":
        hourly = tracker.get_current_droplet_hourly_burn()
        print(f"Current burn rate:")
        print(f"  Hourly: ${hourly:.4f}")
        print(f"  Daily: ${hourly * 24:.2f}")
        print(f"  Monthly: ${hourly * 24 * 30:.2f}")

    elif args.command == "rules":
        if args.partner:
            rules = tracker.get_partner_rules(args.partner)
            print(f"\nCritical Rules for {args.partner}:")
            for rule in rules:
                print(f"  - {rule}")
        else:
            print("Partner terms available for:")
            for p in tracker.terms.get("partners", {}).keys():
                print(f"  - {p}")

    elif args.command == "log":
        if all([args.partner, args.action, args.resource, args.quantity, args.unit, args.cost]):
            entry = tracker.log_cost(
                args.partner, args.action, args.resource,
                args.quantity, args.unit, args.cost
            )
            print(f"Logged: ${entry.total_cost:.4f} for {args.partner}/{args.action}")
        else:
            print("Required: --partner --action --resource --quantity --unit --cost")


if __name__ == "__main__":
    main()
