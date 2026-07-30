from pathlib import Path
import ast

path = Path("ai/factory/runtime.py")
text = path.read_text()

if "self.gap_repair_controller" in text:
    print({
        "status": "SKIPPED",
        "reason": "CONTROLLER_ALREADY_EXISTS"
    })
    raise SystemExit

tree = ast.parse(text)

init_node = None

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "FactoryRuntime":
        for item in node.body:
            if (
                isinstance(item, ast.FunctionDef)
                and item.name == "__init__"
            ):
                init_node = item
                break

if not init_node:
    print({
        "status": "BLOCKED",
        "reason": "INIT_NOT_FOUND"
    })
    raise SystemExit

lines = text.splitlines()

# Insert before end of __init__ body
insert_line = init_node.end_lineno - 1

lines.insert(
    insert_line,
    "        self.gap_repair_controller = FactoryGapRepairController()"
)

if "FactoryGapRepairController" not in text.splitlines()[0:40]:
    lines.insert(
        0,
        "from ai.factory.gap_repair_controller import FactoryGapRepairController"
    )

path.write_text("\n".join(lines) + "\n")

try:
    ast.parse(path.read_text())
    print({
        "status": "PATCHED",
        "next_action": "VERIFY_COMPILE"
    })
except Exception as e:
    print({
        "status": "FAILED",
        "error": str(e)
    })
