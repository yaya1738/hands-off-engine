from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

old = '''"gaps": (
                    assessment_gaps
                    + translated_findings.get(
                        "gaps",
                        [],
                    )
                ),'''

new = '''"gaps": combined_gaps,'''

if old not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old, new, 1)

path.write_text(source)

print({
    "status": "PLANNER_NOW_RECEIVES_COMBINED_GAPS",
    "target": str(path),
})
