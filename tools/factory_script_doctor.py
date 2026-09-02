"""Legacy script-doctor compatibility facade.

The former implementation executed arbitrary repository scripts directly.
Operational execution now belongs to FactoryAuthorityGateway.  This module
remains importable for compatibility but never launches a process.
"""

import sys
from pathlib import Path


def classify_error(text):
    """Classify previously supplied diagnostic text without executing code."""
    text = str(text)
    if "ModuleNotFoundError" in text:
        return "IMPORT ERROR"
    if "SyntaxError" in text:
        return "SYNTAX ERROR"
    if "AttributeError" in text:
        return "MISSING ATTRIBUTE / CONNECTION"
    if "TypeError" in text:
        return "TYPE CONTRACT ERROR"
    if "FileNotFoundError" in text:
        return "MISSING FILE"
    if "KeyError" in text:
        return "DATA CONTRACT ERROR"
    return "UNKNOWN ERROR"


def run_script(script):
    """Fail closed; submit script execution to FactoryAuthorityGateway."""
    return (
        1,
        "",
        "[FACTORY-AUTHORITY] legacy script execution is disabled; "
        "submit through FactoryAuthorityGateway",
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/factory_script_doctor.py <script>")
        raise SystemExit(1)

    script = sys.argv[1]
    print("FACTORY SCRIPT DOCTOR")
    print("=" * 40)
    print("SCRIPT:", script)
    code, output, error = run_script(script)
    print("\nSTATUS: DISABLED")
    print("\nCATEGORY: FACTORY AUTHORITY REQUIRED")
    print("\nTRACEBACK:")
    print(error)
    print("\nNEXT ACTION:")
    print("Submit the diagnostic execution request through FactoryAuthorityGateway.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
