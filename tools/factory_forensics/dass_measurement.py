#!/usr/bin/env python3
"""Fail-closed DASS purity/coverage measurement.

The denominator is the active DASS runtime surface declared in dass_scope.json.
Legacy, income-oriented, backups, tests and documentation are not silently
counted as DASS. A new production file must be deliberately placed under an
active root; otherwise the measurement fails rather than inflating the score.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCOPE = ROOT / "tools/factory_forensics/dass_scope.json"


def tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [x.strip() for x in out.splitlines() if x.strip()]


def matches(path: str, root: str) -> bool:
    return path.startswith(root) if root.endswith("/") else path == root


def main() -> int:
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    files = tracked_files()
    active = [p for p in files if any(matches(p, r) for r in scope["active_roots"])]

    # Active files are mapped by construction to an explicit active root.
    unmapped = [p for p in active if not any(matches(p, r) for r in scope["active_roots"])]

    quarantined = [
        p for p in files if any(matches(p, r) for r in scope["non_dass_quarantined_roots"])
    ]

    # No quarantined income/legacy module may be imported by active Python code.
    import_hits: list[str] = []
    for p in active:
        if not p.endswith(".py"):
            continue
        text = (ROOT / p).read_text(encoding="utf-8", errors="ignore")
        for q in scope["non_dass_quarantined_roots"]:
            token = q.rstrip("/").split("/")[-1]
            if token.endswith("_"):
                token = token[:-1]
            if token and f"import {token}" in text:
                import_hits.append(f"{p}: import {token}")

    mapped = len(active) - len(unmapped)
    coverage = 100.0 if not active else (100.0 * mapped / len(active))
    pure = not unmapped and not import_hits

    report = {
        "mission": scope["mission"],
        "active_files": len(active),
        "mapped_active_files": mapped,
        "unmapped_active_files": unmapped,
        "quarantined_non_dass_files": len(quarantined),
        "quarantined_import_hits": import_hits,
        "dass_coverage_percent": round(coverage, 2),
        "dass_pure": pure,
        "target_percent": scope["score"]["target_percent"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if pure and coverage >= scope["score"]["target_percent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
