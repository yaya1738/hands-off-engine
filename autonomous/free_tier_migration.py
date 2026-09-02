#!/usr/bin/env python3
"""Compatibility facade for the retired free-tier migration path.

Provider installation, credential use, generated-file writes, and migration
mutations belong behind FactoryAuthorityGateway.  This legacy module now
records intent only and fails closed for direct migration.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class FreeTierMigration:
    """Read-only compatibility facade; no package or source-file mutation."""

    def __init__(self):
        self.state_file = BASE_DIR / "state" / "ai_provider_migration.json"
        self.load_state()

    def load_state(self):
        if self.state_file.exists():
            try:
                self.state = json.loads(self.state_file.read_text())
                return
            except (OSError, json.JSONDecodeError):
                pass
        self.state = {
            "migration_started": None,
            "current_provider": "openai",
            "target_providers": ["groq", "google_ai"],
            "monthly_cost_before": 250,
            "monthly_cost_after": 0,
            "monthly_savings": 250,
            "providers_tested": {},
            "providers_enabled": {},
            "callsites_migrated": 0,
            "total_callsites": 0,
            "migration_status": "not_started",
        }

    def save_state(self):
        """Persist only this module's migration metadata."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _blocked(self, provider):
        self.state.setdefault("providers_tested", {})[provider] = {
            "status": "blocked_authority_boundary",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.state["migration_status"] = "blocked_authority_boundary"
        self.save_state()
        print(f"[FACTORY-AUTHORITY] Legacy {provider} setup is disabled; submit provider setup through FactoryAuthorityGateway.")
        return False

    def setup_groq(self):
        return self._blocked("groq")

    def setup_google_ai(self):
        return self._blocked("google_ai")

    def scan_callsites(self):
        """Read-only scan retained for callers that need migration inventory."""
        patterns = ("from openai import", "OpenAI(", "openai.ChatCompletion", "client.chat.completions.create")
        callsites = []
        for py_file in BASE_DIR.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in patterns:
                    if pattern in content:
                        callsites.append({"file": str(py_file), "pattern": pattern})
                        break
            except (OSError, UnicodeDecodeError):
                pass
        self.state["total_callsites"] = len(callsites)
        return callsites

    def create_unified_provider(self):
        """Do not write generated provider code from this legacy path."""
        print("[FACTORY-AUTHORITY] Legacy provider generation is disabled; submit a development request through FactoryAuthorityGateway.")
        return None

    def run_migration(self):
        """Fail closed; no packages, credentials, or source files are mutated."""
        self.state["migration_started"] = datetime.now(timezone.utc).isoformat()
        self.state["migration_status"] = "blocked_authority_boundary"
        self.save_state()
        print("[FACTORY-AUTHORITY] Legacy free-tier migration is disabled; submit migration work through FactoryAuthorityGateway.")
        return False

    def get_status(self):
        return self.state


if __name__ == "__main__":
    raise SystemExit(0 if FreeTierMigration().run_migration() else 1)
