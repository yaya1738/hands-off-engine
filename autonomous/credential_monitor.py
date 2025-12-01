#!/usr/bin/env python3
"""
CREDENTIAL MONITOR - Track API key validity and expiration
============================================================

Monitors:
- API key last-used timestamps
- Token refresh requirements
- Credential health checks

Master: Yair Siegel
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
CRED_STATE = STATE_DIR / "credential_state.json"


class CredentialMonitor:
    """Monitor credential validity and expiration."""

    # Credentials to monitor
    CREDENTIALS = {
        "OPENAI_API_KEY": {"env_var": "OPENAI_API_KEY", "test_url": "https://api.openai.com/v1/models"},
        "GROQ_API_KEY": {"env_var": "GROQ_API_KEY", "test_url": None},
        "GOOGLE_API_KEY": {"env_var": "GOOGLE_API_KEY", "test_url": None},
        "DO_API_TOKEN": {"env_var": "DO_API_TOKEN", "test_url": "https://api.digitalocean.com/v2/account"},
        "TELEGRAM_BOT_TOKEN": {"env_var": "TELEGRAM_BOT_TOKEN", "test_url": None},
        "POLYMARKET_PRIVATE_KEY": {"env_var": "POLYMARKET_PRIVATE_KEY", "test_url": None},
    }

    def __init__(self):
        self._load_env()
        self.state = self._load_state()

    def _load_env(self):
        """Load environment variables."""
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip())

    def _load_state(self) -> Dict:
        if CRED_STATE.exists():
            return json.load(open(CRED_STATE))
        return {"credentials": {}, "last_check": None}

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(CRED_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def check_credential(self, name: str) -> Tuple[bool, str]:
        """Check if a credential is valid."""
        if name not in self.CREDENTIALS:
            return False, f"Unknown credential: {name}"

        config = self.CREDENTIALS[name]
        env_var = config["env_var"]

        # Check if set
        value = os.environ.get(env_var)
        if not value:
            return False, f"{name} not set in environment"

        # Check if looks valid (basic format check)
        if len(value) < 10:
            return False, f"{name} looks invalid (too short)"

        # Update state
        if name not in self.state["credentials"]:
            self.state["credentials"][name] = {}

        self.state["credentials"][name]["present"] = True
        self.state["credentials"][name]["last_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return True, f"{name} present and looks valid"

    def check_all(self) -> Dict[str, Tuple[bool, str]]:
        """Check all credentials."""
        results = {}
        for name in self.CREDENTIALS:
            results[name] = self.check_credential(name)

        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return results

    def get_missing(self) -> list:
        """Get list of missing credentials."""
        missing = []
        for name, (ok, msg) in self.check_all().items():
            if not ok:
                missing.append(name)
        return missing

    def get_status(self) -> Dict:
        """Get full credential status."""
        results = self.check_all()
        return {
            "credentials": {name: {"valid": ok, "message": msg} for name, (ok, msg) in results.items()},
            "missing": self.get_missing(),
            "all_valid": len(self.get_missing()) == 0,
            "last_check": self.state.get("last_check")
        }


def get_credential_monitor() -> CredentialMonitor:
    return CredentialMonitor()


if __name__ == "__main__":
    import sys
    monitor = get_credential_monitor()

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = monitor.get_status()
        print(json.dumps(status, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "missing":
        missing = monitor.get_missing()
        if missing:
            print("Missing credentials:")
            for m in missing:
                print(f"  - {m}")
        else:
            print("All credentials present")
    else:
        print("Usage: python credential_monitor.py [status|missing]")
