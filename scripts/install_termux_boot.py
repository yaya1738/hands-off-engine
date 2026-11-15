#!/usr/bin/env python3
"""Install the Termux:Boot auto-start script.

Copies ``termux/boot-start.sh`` into the Termux boot directory
(``~/.termux/boot/``) with safe permissions.

Path-safety contract (fixes the relative-invocation blocker from the
scheduler supervision v2 audit):

- Every path is resolved to an absolute path from ``__file__`` at startup,
  BEFORE any directory change or subprocess call.
- The script never relies on the relative invocation path (``$0`` /
  ``sys.argv[0]``) after any ``chdir`` — it does not chdir at all.
- Source and destination locations are computed once and used consistently.
"""
import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

# Resolve the repository root absolutely at import time, before any
# directory changes. This is the ONLY path anchor.
ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "termux" / "boot-start.sh"
DEFAULT_DEST_DIR = Path.home() / ".termux" / "boot"


def install(dest_dir=None, dry_run=False):
    """Copy boot-start.sh into the Termux boot directory.

    Returns (installed: bool, message: str).
    """
    dest_dir = Path(dest_dir) if dest_dir else DEFAULT_DEST_DIR
    dest = dest_dir / "boot-start.sh"

    if not SOURCE.is_file():
        return False, f"source not found: {SOURCE}"

    if dry_run:
        return True, f"would copy {SOURCE} -> {dest}"

    dest_dir.mkdir(parents=True, exist_ok=True)
    # Copy to a temp file in the same directory, then atomically replace —
    # a partially-written boot script must never be left behind.
    tmp = dest.with_suffix(".tmp")
    shutil.copyfile(SOURCE, tmp)
    tmp.chmod(stat.S_IRWXU)  # owner-only rwx: boot scripts are executable
    os.replace(tmp, dest)
    return True, f"installed {SOURCE} -> {dest}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=None,
                        help="destination directory (default: ~/.termux/boot)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would be done without writing")
    args = parser.parse_args(argv)

    ok, message = install(dest_dir=args.dest, dry_run=args.dry_run)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
