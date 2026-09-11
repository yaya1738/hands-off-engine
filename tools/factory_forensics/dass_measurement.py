#!/usr/bin/env python3
"""Fail-closed measurement of the declared DASS production surface.

DASS is a bounded autonomous runtime, not the entire historical repository.
Every declared active file is measured, and every operational-looking path
outside the declared surface is treated as an explicit measurement gap rather
than silently ignored. Quarantined dependencies also fail the measurement.
"""
from __future__ import annotations

import ast
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


def classify(path: str, scope: dict) -> str:
    if any(matches(path, r) for r in scope["active_roots"]):
        return "dass"
    if any(matches(path, r) for r in scope["non_dass_quarantined_roots"]):
        return "quarantined"
    if (path.startswith(("tests/", ".github/", "docs/"))
        or path.endswith((".md", ".txt", ".rst"))
        or path.startswith(("examples/", "samples/"))):
        return "support"
    return "unclassified"


def python_imports(path: str) -> list[str]:
    try:
        tree = ast.parse(
            (ROOT / path).read_text(encoding="utf-8", errors="ignore"),
            filename=path,
        )
    except SyntaxError:
        return [f"{path}: syntax-error"]
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def main() -> int:
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    files = tracked_files()
    classes = {p: classify(p, scope) for p in files}
    dass = [p for p, c in classes.items() if c == "dass"]
    quarantined = [p for p, c in classes.items() if c == "quarantined"]
    unclassified = [p for p, c in classes.items() if c == "unclassified"]

    # Executable/operational files outside the declared DASS surface are
    # measurement gaps. They must be explicitly promoted, quarantined, or
    # otherwise classified; they cannot disappear from the denominator.
    operational_unclassified = [
        p for p in unclassified
        if p.endswith((".py", ".sh", ".service", ".yml", ".yaml"))
    ]

    prefixes = [r.rstrip("/").replace("/", ".") for r in scope["non_dass_quarantined_roots"]]
    import_hits: list[str] = []
    for p in dass:
        if not p.endswith(".py"):
            continue
        for module in python_imports(p):
            if any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes):
                import_hits.append(f"{p}: {module}")

    active_unmapped = [p for p in dass if not (ROOT / p).exists()]
    pure = not operational_unclassified and not active_unmapped and not import_hits
    measured = len(dass)
    denominator = measured + len(operational_unclassified)
    coverage = 100.0 if denominator == 0 or not operational_unclassified else 100.0 * measured / denominator
    report = {
        "mission": scope["mission"],
        "tracked_files": len(files),
        "dass_runtime_files": measured,
        "quarantined_non_dass_files": len(quarantined),
        "support_files": sum(c == "support" for c in classes.values()),
        "unclassified_files": unclassified,
        "operational_unclassified_files": operational_unclassified,
        "quarantined_import_hits": import_hits,
        "active_unmapped_files": active_unmapped,
        "dass_coverage_percent": round(coverage, 2),
        "dass_pure": pure,
        "target_percent": scope["score"]["target_percent"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if pure and coverage >= scope["score"]["target_percent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
