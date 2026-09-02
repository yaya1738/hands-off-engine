"""Read-only compatibility facade for legacy constructor repair.

Repository mutation and validation execution belong to FactoryAuthorityGateway.
"""
from pathlib import Path
import re

FILE = Path("ai/factory/runtime.py")


def find_pipeline_block():
    try:
        text = FILE.read_text()
    except OSError:
        return None
    pattern = r"self\.development_pipeline\s*=\s*FactoryDevelopmentPipeline\s*\(.*?\)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(0) if match else None


def main():
    block = find_pipeline_block()
    if block:
        print("Detected constructor block:")
        print(block)
    print("[FACTORY-AUTHORITY] constructor repair is disabled; submit through FactoryAuthorityGateway")
    return False


if __name__ == "__main__":
    main()
