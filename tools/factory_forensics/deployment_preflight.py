#!/usr/bin/env python3
"""Deterministic, fail-closed preflight for governed production deployment.

This intentionally performs no deployment, credential access, or financial
execution. It catches repository-side blockers before an external authority
is required.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {".py", ".yml", ".yaml", ".sh", ".service", ".toml"}
GUARD_PATH = Path("tools/factory_forensics/live_mutation_guard.py")


def files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.relative_to(root) == GUARD_PATH:
            continue
        yield path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    workflow = root / ".github/workflows/autonomous-authority-reconcile.yml"
    deploy = root / ".github/workflows/production-deploy.yml"
    guard = root / "tools/factory_forensics/live_mutation_guard.py"
    authority = root / "ai/factory/live_order_authority.py"

    for required in (workflow, deploy, guard, authority):
        if not required.is_file():
            errors.append(f"missing required safety/deployment file: {required.relative_to(root)}")

    if authority.is_file():
        text = authority.read_text(encoding="utf-8")
        if "deny" not in text.lower() or "fail" not in text.lower():
            errors.append("live-order authority does not visibly declare fail-closed/deny semantics")

    # Repository-side direct mutation must remain absent. The approved authority
    # currently contains no exchange mutation implementation, so every match is
    # a blocker rather than something to whitelist. The guard implementation is
    # itself scanner code and must not be reported as a production mutation path.
    pattern = re.compile(r"\bpost_order\s*\(")
    for path in files(root):
        if path == authority:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            errors.append(f"direct live-order mutation remains: {path.relative_to(root)}")

    if errors:
        print("DEPLOYMENT_PREFLIGHT_BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("DEPLOYMENT_PREFLIGHT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
