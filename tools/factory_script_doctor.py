import subprocess
import sys
import traceback
from pathlib import Path


def classify_error(text):
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
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
        )

        return (
            result.returncode,
            result.stdout,
            result.stderr,
        )

    except Exception:
        return (
            1,
            "",
            traceback.format_exc(),
        )


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 tools/factory_script_doctor.py <script>"
        )
        raise SystemExit(1)

    script = sys.argv[1]

    if not Path(script).exists():
        print("SCRIPT NOT FOUND:", script)
        raise SystemExit(1)

    print("FACTORY SCRIPT DOCTOR")
    print("=" * 40)
    print("SCRIPT:", script)

    code, output, error = run_script(script)

    if code == 0:
        print("\nSTATUS: HEALTHY")
        print(output)
        return

    print("\nSTATUS: FAILED")

    combined = output + "\n" + error

    print("\nCATEGORY:")
    print(classify_error(combined))

    print("\nTRACEBACK:")
    print(error)

    print("\nNEXT ACTION:")
    print(
        "Inspect the classified failure and create a proper Factory change, "
        "not a disposable patch script."
    )


if __name__ == "__main__":
    main()
