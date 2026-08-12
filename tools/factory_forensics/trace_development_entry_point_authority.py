from pathlib import Path
import ast
import re

ROOT = Path(".")
TARGET = ROOT / "ai/factory/development_entry_point.py"


def read(path):
    return path.read_text(errors="replace")


def find_class_and_methods(tree):
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = {}
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods[child.name] = child.lineno
            result[node.name] = methods
    return result


def find_references():
    refs = []
    for path in ROOT.rglob("*.py"):
        if "tools/factory_forensics" in str(path):
            continue

        try:
            text = read(path)
        except Exception:
            continue

        for lineno, line in enumerate(text.splitlines(), 1):
            if "FactoryDevelopmentEntryPoint" in line:
                refs.append((str(path), lineno, line.strip()))

            if re.search(r"\.submit_objective\s*\(", line):
                refs.append((str(path), lineno, line.strip()))

    return refs


def main():
    print("=== FACTORY DEVELOPMENT ENTRY POINT AUTHORITY TRACE ===")
    print(f"Repository: {ROOT.resolve()}")
    print()

    if not TARGET.exists():
        print("[ERROR] Target does not exist:")
        print(f"  {TARGET}")
        return 2

    print("=== TARGET ===")
    print(f"  {TARGET}")
    print()

    source = read(TARGET)
    tree = ast.parse(source)

    classes = find_class_and_methods(tree)

    for name, methods in classes.items():
        if name == "FactoryDevelopmentEntryPoint":
            print(f"--- {name} ---")
            for method, lineno in methods.items():
                print(f"  {method}() @ line {lineno}")
            print()

    print("=== DEVELOPMENT-INTENT METHOD ===")

    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "submit_objective"
        ):
            print(f"--- submit_objective() @ line {node.lineno} ---")

            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)
                    elif isinstance(child.func, ast.Name):
                        calls.append(child.func.id)

            interesting = [
                c for c in calls
                if any(
                    token in c.lower()
                    for token in (
                        "assessment",
                        "roadmap",
                        "design",
                        "specification",
                        "development",
                        "bridge",
                        "submit",
                        "request",
                    )
                )
            ]

            for call in sorted(set(interesting)):
                print(f"  call: {call}()")

            print()

    print("=== CROSS-FILE CONSUMERS ===")

    refs = find_references()

    if not refs:
        print("  NONE FOUND")
    else:
        for path, lineno, line in refs:
            print(f"  {path}:{lineno}: {line}")

    print()

    print("=== AUTHORITY SIGNALS ===")

    gateway = []
    external = []
    downstream = []
    internal = []

    for path, lineno, line in refs:
        lower = line.lower()

        if "authoritygateway" in lower:
            gateway.append((path, lineno, line))
        elif any(
            token in lower
            for token in ("cli", "external", "interface", "request", "service", "api")
        ):
            external.append((path, lineno, line))
        elif any(
            token in lower
            for token in ("pipeline", "bridge", "design", "specification", "improvement")
        ):
            downstream.append((path, lineno, line))
        else:
            internal.append((path, lineno, line))

    print(f"Gateway signals:     {len(gateway)}")
    print(f"External signals:    {len(external)}")
    print(f"Downstream signals:  {len(downstream)}")
    print(f"Internal signals:    {len(internal)}")
    print()

    print("=== DECISION RULES ===")
    print("[RULE] External development intent must converge on FactoryAuthorityGateway.")
    print("[RULE] Internal construction components remain downstream.")
    print("[RULE] Existing runtime control-loop callers are not migrated merely for convergence.")
    print("[RULE] Do not duplicate discovery, planning, translation, approval, or tracking.")
    print("[RULE] This audit performs no production migration.")
    print()

    if gateway:
        classification = "AUTHORIZED GATEWAY"
    elif external:
        classification = "POTENTIAL EXTERNAL BYPASS"
    elif downstream:
        classification = "DOWNSTREAM DEVELOPMENT CONSTRUCTION"
    else:
        classification = "UNCLASSIFIED"

    print("=== AUTHORITY CLASSIFICATION ===")
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
