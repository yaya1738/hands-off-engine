#!/usr/bin/env python3
"""Fail closed when production source directly posts Polymarket orders.

The guard is intentionally a deployment gate, not an execution mechanism.
Live order mutation must enter an explicitly approved authority capability.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

POST_ORDER = re.compile(r"\bpost_order\s*\(")
SKIP_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__"}
SKIP_SUFFIXES = {".md", ".rst", ".txt", ".json", ".lock"}
SKIP_DIRECTORIES = {".github"}
TEST_PARTS = {"tests", "test"}
GUARD_PATH = Path("tools/factory_forensics/live_mutation_guard.py")


def iter_source(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if any(part in TEST_PARTS for part in path.parts):
            continue
        if path.relative_to(root) == GUARD_PATH:
            continue
        yield path


def find_violations(root: Path) -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    for path in iter_source(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if POST_ORDER.search(line):
                violations.append((path.relative_to(root), lineno, line.strip()))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    violations = find_violations(root)
    if violations:
        print("LIVE_MUTATION_GUARD_FAILED: direct post_order() usage detected")
        for path, lineno, line in violations:
            print(f"- {path}:{lineno}: {line}")
        print("Deployment is blocked until every live-order mutation path is routed through an approved authority capability.")
        return 1
    print("LIVE_MUTATION_GUARD_OK: no direct post_order() usage detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
