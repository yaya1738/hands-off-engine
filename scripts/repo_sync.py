#!/usr/bin/env python3
"""Safely fast-forward a clean Termux checkout to origin/main.

Never resets, cleans, or discards local work. If the checkout is dirty or
diverged, it records a bounded skip and leaves the runtime untouched.
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "repo_sync_state.json"


def run(*args):
    return subprocess.run(
        list(args), cwd=ROOT, text=True, capture_output=True, timeout=30
    )


def sync_once():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "status": "skipped"}

    if not (ROOT / ".git").exists():
        result["reason"] = "not_git_checkout"
    else:
        fetch = run("git", "fetch", "origin", "main", "--quiet")
        if fetch.returncode != 0:
            result["reason"] = "fetch_failed"
        else:
            dirty = run("git", "status", "--porcelain")
            branch = run("git", "branch", "--show-current")
            if dirty.stdout.strip():
                result["reason"] = "working_tree_dirty"
            elif branch.stdout.strip() != "main":
                result["reason"] = "not_on_main"
            else:
                ff = run("git", "merge", "--ff-only", "origin/main")
                if ff.returncode == 0:
                    result["status"] = "updated" if "Already up to date" not in ff.stdout else "current"
                else:
                    result["reason"] = "not_fast_forward"

    STATE.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(sync_once(), sort_keys=True))
