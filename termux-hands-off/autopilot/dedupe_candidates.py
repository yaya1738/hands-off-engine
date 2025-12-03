import os, json

BASE = os.path.expanduser("~/hands-off/autopilot")
CAND = os.path.join(BASE, "candidates.jsonl")

def main():
    if not os.path.exists(CAND):
        return
    seen = set()
    dedup = []
    with open(CAND, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            key = str(j.get("key","unknown"))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(line)
    tmp = CAND + ".tmp"
    with open(tmp, "w") as f:
        for line in dedup:
            f.write(line + "\n")
    os.replace(tmp, CAND)

if __name__ == "__main__":
    main()
