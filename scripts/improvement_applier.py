#!/usr/bin/env python3
"""Improvement Applier — execute safe bounded improvements.

Takes improvement candidates and applies the ones that can be executed
safely without human approval. This closes the observe→act gap in the
self-improvement loop.

Safe actions (auto-execute):
  - update_documentation: append findings to docs
  - archive_state: compress old state files
  - update_readme: add/update README sections
  - generate_report: create analysis report files
  - fix_config: update configuration based on detected issues
  - log_analysis: write bounded observational summaries

Actions that write to tests/ require explicit approval; canonical bus pruning is disabled and must use a separately reviewed archival procedure.

Risky actions (queue for operator approval):
  - code_change: modify source code
  - add_dependency: add new dependencies
  - network_action: make outbound requests

Design constraints:
  - All writes go to state/, docs/, or config/ — never to scripts/ or tests/
  - Each improvement is idempotent (safe to re-run)
  - Improvement impact is tracked for the feedback loop
  - Fail-closed: any unexpected error stops the cycle
"""

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
APPLIER_STATE = STATE / "improvement_applier_state.json"
APPROVAL_QUEUE = STATE / "improvement_approval_queue.json"
FEEDBACK_FILE = STATE / "improvement_feedback.json"
DOCS_DIR = ROOT / "docs"

# Actions the applier can execute without approval
SAFE_ACTIONS = {
    "update_documentation",
    "archive_state",
    "update_readme",
    "generate_report",
    "fix_config",
    "log_analysis",
}

# Actions that require operator approval
RISKY_ACTIONS = {
    "code_change",
    "add_dependency",
    "network_action",
    "delete_file",
    "add_test",
    "clean_bus",
}

# Directories the applier may write to
ALLOWED_WRITE_DIRS = frozenset({
    ROOT / "state",
    ROOT / "docs",
    ROOT / "config",
    ROOT / "ai",
})


def load_state():
    if APPLIER_STATE.exists():
        try:
            return json.loads(APPLIER_STATE.read_text())
        except Exception:
            pass
    return {"applied": [], "queued": [], "history": []}