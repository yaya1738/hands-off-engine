#!/usr/bin/env python3
"""
Integrate Unified AI into all system components.
Injects the unified AI import into scripts that don't have it.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path("/root/hands-off-engine")
UNIFIED_IMPORT = """
# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"
"""

def integrate_script(script_path: Path) -> bool:
    """Add unified AI import to a script if not present."""
    content = script_path.read_text()
    
    # Skip if already integrated
    if "unified_ai" in content:
        return False
    
    # Skip if not a real script (no imports)
    if "import " not in content:
        return False
    
    # Find first import statement and add unified AI after shebang/docstring
    lines = content.split('\n')
    insert_idx = 0
    
    # Skip shebang
    if lines[0].startswith('#!'):
        insert_idx = 1
    
    # Skip docstrings
    in_docstring = False
    for i, line in enumerate(lines[insert_idx:], insert_idx):
        if '"""' in line or "'''" in line:
            if in_docstring:
                insert_idx = i + 1
                break
            else:
                in_docstring = True
        elif not in_docstring and (line.startswith('import ') or line.startswith('from ')):
            insert_idx = i
            break
    
    # Insert unified AI import
    lines.insert(insert_idx, UNIFIED_IMPORT)
    
    script_path.write_text('\n'.join(lines))
    return True

def main():
    scripts_dir = REPO_ROOT / "scripts"
    autonomous_dir = REPO_ROOT / "autonomous"
    
    integrated = []
    
    for script in scripts_dir.glob("*.py"):
        if integrate_script(script):
            integrated.append(str(script.name))
    
    for script in autonomous_dir.glob("*.py"):
        if integrate_script(script):
            integrated.append(str(script.name))
    
    print(f"Integrated {len(integrated)} scripts:")
    for s in integrated:
        print(f"  ✓ {s}")

if __name__ == "__main__":
    main()
