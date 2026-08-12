from pathlib import Path
import ast

ROOT = Path(".")
TARGET = ROOT / "ai/factory/development_entry_point.py"


def classify_path(path: Path):
    text = str(path)

    if text.startswith("tests/") or "/tests/" in text:
        return "TEST"

    if text.startswith("tools/") or "/tools/" in text:
        return "FORENSIC_OR_DEVELOPMENT_TOOL"

    if text.startswith("ai/factory/"):
        return "PRODUCTION_FACTORY"

    return "OTHER"


def find_consumers():
    consumers = []

    for path in ROOT.rglob("*.py"):
        if "tools/factory_forensics" in str(path):
            continue

        try:
            source = path.read_text(errors="replace")
        except Exception:
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # FactoryDevelopmentEntryPoint(...)
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "FactoryDevelopmentEntryPoint"
                ):
                    consumers.append(
                        (
                            path,
                            node.lineno,
                            "constructor",
                        )
                    )

                # factory.submit_objective(...)
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "submit_objective"
                ):
                    consumers.append(
                        (
                            path,
                            node.lineno,
                            "submit_objective",
                        )
                    )

    return consumers


def main():
    print("=== FACTORY DEVELOPMENT ENTRY POINT CONSUMER AUTHORITY CLASSIFICATION ===")
    print(f"Repository: {ROOT.resolve()}")
    print()

    if not TARGET.exists():
        print("[ERROR] Target missing:")
        print(f"  {TARGET}")
        return 2

    consumers = find_consumers()

    buckets = {
        "PRODUCTION_FACTORY": [],
        "TEST": [],
        "FORENSIC_OR_DEVELOPMENT_TOOL": [],
        "OTHER": [],
    }

    for path, lineno, kind in consumers:
        classification = classify_path(path)
        buckets[classification].append(
            (path, lineno, kind)
        )

    print("=== CONSUMERS ===")

    for classification, entries in buckets.items():
        print()
        print(f"--- {classification} ({len(entries)}) ---")

        if not entries:
            print("  NONE")
            continue

        for path, lineno, kind in entries:
            print(
                f"  {path}:{lineno} [{kind}]"
            )

    print()
    print("=== AUTHORITY ANALYSIS ===")

    production = buckets["PRODUCTION_FACTORY"]
    tests = buckets["TEST"]
    tools = buckets["FORENSIC_OR_DEVELOPMENT_TOOL"]

    print(f"Production consumers: {len(production)}")
    print(f"Test consumers:       {len(tests)}")
    print(f"Tool consumers:       {len(tools)}")

    print()

    if production:
        print("[REVIEW REQUIRED] Production Factory consumers exist.")
        print("[OBSERVE] These callers require authority classification.")
        classification = "PRODUCTION-CONSUMER-REVIEW"
    else:
        print("[PASS] No production Factory consumer of FactoryDevelopmentEntryPoint found.")
        print("[PASS] No production submit_objective() caller found.")
        print("[PASS] Tests/tools do not constitute external production ingress.")
        classification = "NO-PRODUCTION-INGRESS"

    print()
    print("=== AUTHORITY CLOSURE RULES ===")
    print("[RULE] FactoryAuthorityGateway remains the external development-ingress authority.")
    print("[RULE] Test consumers are not production authority.")
    print("[RULE] Forensic/development tools are not production authority.")
    print("[RULE] A production caller would require separate authority analysis.")
    print("[RULE] Do not migrate or duplicate development processing merely for convergence.")
    print()

    print("=== CLOSURE DECISION ===")
    print(classification)

    print()
    print("=== READ-ONLY RESULT ===")
    print("PASS")
    print("No files were modified.")
    print("No files were staged.")
    print("No commit was created.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
