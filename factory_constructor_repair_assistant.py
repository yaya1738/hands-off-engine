from pathlib import Path
import re
import subprocess


FILE = Path("ai/factory/runtime.py")


def find_pipeline_block():
    text = FILE.read_text()

    pattern = r"self\.development_pipeline\s*=\s*FactoryDevelopmentPipeline\s*\(.*?\)"

    match = re.search(
        pattern,
        text,
        re.DOTALL,
    )

    return match.group(0) if match else None


def main():
    block = find_pipeline_block()

    if not block:
        print("No FactoryDevelopmentPipeline constructor found")
        return

    print("Detected constructor block:")
    print("-" * 40)
    print(block)
    print("-" * 40)

    replacement = (
        "self.development_pipeline = "
        "FactoryDevelopmentPipeline()"
    )

    print("\nProposed replacement:")
    print(replacement)

    answer = input(
        "\nApply this change? (yes/no): "
    )

    if answer.lower() != "yes":
        print("No changes made")
        return

    text = FILE.read_text()

    text = text.replace(
        block,
        replacement,
        1,
    )

    FILE.write_text(text)

    print("Change applied")

    result = subprocess.run(
        [
            "python",
            "-m",
            "py_compile",
            str(FILE),
        ]
    )

    if result.returncode == 0:
        print("Validation passed")
    else:
        print("Validation failed")


if __name__ == "__main__":
    main()
