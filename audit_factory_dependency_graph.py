import ast
from pathlib import Path

ROOT = Path("ai/factory")

targets = [
    "artifact_registry",
    "decision_option_adapter",
    "development_advisor",
    "development_translator",
    "development_tracker",
    "lifecycle_trace",
    "improvement_queue",
]

for target in targets:
    print("\n====", target, "====")

    found = False

    for file in ROOT.glob("*.py"):
        try:
            text = file.read_text()
        except:
            continue

        if target in text:
            for i,line in enumerate(text.splitlines(),1):
                if target in line:
                    print(
                        file.name,
                        i,
                        line.strip()
                    )
                    found = True

    if not found:
        print("NO REFERENCES")
