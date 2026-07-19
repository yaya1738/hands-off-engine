import subprocess
import sys


def run(cmd):
    print("\n$", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/factory_commit.py \"commit message\"")
        raise SystemExit(1)

    message = sys.argv[1]

    print("FACTORY COMMIT CHECKPOINT")
    print("=" * 40)

    run(["git", "status", "--short"])

    print("\nAdding tracked Factory changes...")
    run(["git", "add", "-A"])

    print("\nCreating commit...")
    run([
        "git",
        "commit",
        "-m",
        message
    ])

    print("\nCOMMIT COMPLETE")


if __name__ == "__main__":
    main()
