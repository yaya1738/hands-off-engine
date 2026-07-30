from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

anchor = (
    '        improvement_cycle["capability_gap_analysis"] = capability_gap_analysis\n'
)

insert = (
    '        improvement_cycle["capability_gap_analysis"] = capability_gap_analysis\n'
    '        improvement_cycle["capability_context"] = capability_context\n'
)

if '"capability_context"] = capability_context' in text:
    print("ALREADY_PRESENT")
    raise SystemExit(0)

if anchor not in text:
    print("ANCHOR_NOT_FOUND")
    raise SystemExit(1)

text = text.replace(anchor, insert, 1)

path.write_text(text)

print("CAPABILITY_CONTEXT_OUTPUT_FIXED")
