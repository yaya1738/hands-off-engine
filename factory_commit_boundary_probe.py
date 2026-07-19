from pathlib import Path
import ast

runtime = Path("ai/factory/runtime.py").read_text(errors="ignore")

modules = []

tree = ast.parse(runtime)

for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        if node.module and node.module.startswith("ai.factory"):
            modules.append(node.module)

print("FACTORY COMMIT BOUNDARY")
print("=" * 35)

checks = [
    ("LIFECYCLE TRACE IMPORTED",
     "ai.factory.lifecycle_trace" in modules),

    ("RUNTIME UPDATED FOR TRACE",
     "lifecycle_trace" in runtime),

    ("NEW TRACE FILE EXISTS",
     Path("ai/factory/lifecycle_trace.py").exists()),
]

for name, value in checks:
    print(name + ":", "YES" if value else "NO")

print("DONE")
