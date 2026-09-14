#!/usr/bin/env python3
"""
API QUOTA MONITOR - Track and predict API quota exhaustion
===========================================================

Monitors:
- OpenAI API usage
- Groq API usage
- Google AI usage
- Anthropic API usage

Predicts when quotas will exhaust based on usage patterns.

Master: Yair Siegel
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

QUOTA_STATE = STATE_DIR / "api_quota_state.json"
QUOTA_HISTORY = STATE_DIR / "api_quota_history.jsonl"


class QuotaMonitor:
    """Monitor and predict API quota exhaustion."""

    # Known quota limits (update as needed)
    KNOWN_LIMITS = {
        "openai": {
            "requests_per_min": 60,
            "tokens_per_min": 90000,
            "requests_per_day": 10000,
            "monthly_spend_limit": 120.0  # dollars
        },
        "groq": {
            "requests_per_min": 30,
            "tokens_per_min": 6000,
            "requests_per_day": 14400,
            "monthly_spend_limit": 0  # free tier
        },
        "google": {
            "requests_per_min": 60,
            "requests_per_day": 1500,
            "monthly_spend_limit": 0  # free tier
        },
        "anthropic": {
            "requests_per_min": 60,
            "tokens_per_min": 100000,
            "monthly_spend_limit": 100.0
        }
    }

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if QUOTA_STATE.exists():
            return json.load(open(QUOTA_STATE))
        return {
            "providers": {},
            "last_check": None,
            "alerts": []
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(QUOTA_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def record_usage(self, provider: str, requests: int = 1, tokens: int = 0, cost: float = 0):
        """Record API usage."""
        now = datetime.now(timezone.utc)

        if provider not in self.state["providers"]:
            self.state["providers"][provider] = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "today_requests": 0,
                "today_tokens": 0,
                "today_cost": 0,
                "last_reset": now.date().isoformat(),
                "usage_history": []
            }

        p = self.state["providers"][provider]

        # Reset daily counters if new day
        if p["last_reset"] != now.date().isoformat():
            p["today_requests"] = 0
            p["today_tokens"] = 0
            p["today_cost"] = 0
            p["last_reset"] = now.date().isoformat()

        p["total_requests"] += requests
        p["total_tokens"] += tokens
        p["total_cost"] += cost
        p["today_requests"] += requests
        p["today_tokens"] += tokens
        p["today_cost"] += cost

        # Keep last 100 usage entries
        p["usage_history"].append({
            "timestamp": now.isoformat(),
            "requests": requests,
            "tokens": tokens,
            "cost": cost
        })
        p["usage_history"] = p["usage_history"][-100:]

        self._save_state()

        # Log to history
        with open(QUOTA_HISTORY, 'a') as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "provider": provider,
                "requests": requests,
                "tokens": tokens,
                "cost": cost
            }) + '\n')

    def check_quota(self, provider: str) -> Tuple[bool, str, float]:
        """
        Check if quota is OK for a provider.
        Returns: (ok, message, percentage_used)
        """
        if provider not in self.KNOWN_LIMITS:
            return True, "Unknown provider - no limits known", 0

        limits = self.KNOWN_LIMITS[provider]

        if provider not in self.state["providers"]:
            return True, "No usage recorded", 0

        p = self.state["providers"][provider]

        # Check daily requests
        daily_limit = limits.get("requests_per_day", float('inf'))
        daily_used = p.get("today_requests", 0)
        daily_pct = (daily_used / daily_limit * 100) if daily_limit else 0

        if daily_pct >= 90:
            return False, f"Daily request limit {daily_pct:.0f}% used", daily_pct

        # Check monthly spend
        monthly_limit = limits.get("monthly_spend_limit", float('inf'))
        monthly_spent = p.get("total_cost", 0)  # Approximation
        monthly_pct = (monthly_spent / monthly_limit * 100) if monthly_limit else 0

        if monthly_pct >= 80:
            return False, f"Monthly spend {monthly_pct:.0f}% used (${monthly_spent:.2f})", monthly_pct

        return True, f"OK ({daily_pct:.0f}% daily, ${monthly_spent:.2f} spent)", max(daily_pct, monthly_pct)

    def predict_exhaustion(self, provider: str) -> Optional[datetime]:
        """Predict when quota will be exhausted based on usage pattern."""
        if provider not in self.state["providers"]:
            return None

        p = self.state["providers"][provider]
        history = p.get("usage_history", [])

        if len(history) < 5:
            return None  # Not enough data

        # Calculate average requests per hour
        now = datetime.now(timezone.utc)
        recent = [h for h in history if (now - datetime.fromisoformat(h["timestamp"].replace('Z', '+00:00'))).total_seconds() < 86400]

        if not recent:
            return None

        total_requests = sum(h["requests"] for h in recent)
        hours = len(recent) / 4  # Rough estimate
        if hours < 1:
            hours = 1

        requests_per_hour = total_requests / hours

        # Calculate remaining quota
        limits = self.KNOWN_LIMITS.get(provider, {})
        daily_limit = limits.get("requests_per_day", 10000)
        remaining = daily_limit - p.get("today_requests", 0)

        if requests_per_hour <= 0:
            return None

        hours_until_exhaustion = remaining / requests_per_hour

        return now + timedelta(hours=hours_until_exhaustion)

    def get_status(self) -> Dict:
        """Get full quota status."""
        status = {"providers": {}, "alerts": []}

        for provider in self.KNOWN_LIMITS:
            ok, msg, pct = self.check_quota(provider)
            exhaustion = self.predict_exhaustion(provider)

            status["providers"][provider] = {
                "ok": ok,
                "message": msg,
                "percentage_used": pct,
                "predicted_exhaustion": exhaustion.isoformat() if exhaustion else None
            }

            if not ok:
                status["alerts"].append(f"{provider}: {msg}")
            elif exhaustion and (exhaustion - datetime.now(timezone.utc)).total_seconds() < 7200:
                status["alerts"].append(f"{provider}: Exhaustion predicted in {(exhaustion - datetime.now(timezone.utc)).total_seconds()/3600:.1f}h")

        return status


def get_quota_monitor() -> QuotaMonitor:
    return QuotaMonitor()


if __name__ == "__main__":
    import sys
    monitor = get_quota_monitor()

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = monitor.get_status()
        print(json.dumps(status, indent=2))
    else:
        print("Usage: python api_quota_monitor.py status")
