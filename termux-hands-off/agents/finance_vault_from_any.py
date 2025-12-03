import os, json, pathlib, re, sys

HOME = pathlib.Path.home()
CANDIDATES = [
    HOME/".config"/"keys.vault",
    *sorted((HOME/".config").glob("keys.vault.bak.*"), reverse=True)
]
OUT = HOME/".config"/"hands-off"/"vault.json"

def load_candidate(path: pathlib.Path):
    if not path.exists():
        return None
    txt = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not txt:
        return None
    # Try JSON first
    try:
        obj = json.loads(txt)
        if isinstance(obj, dict): return obj
    except Exception:
        pass
    # Fallback: .env / KEY=VALUE parser
    out = {}
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*(.*)$', line)
        if not m: continue
        k, v = m.group(1), m.group(2).strip()
        # strip optional quotes
        if len(v) >= 2 and ((v[0]==v[-1]=="'") or (v[0]==v[-1]=='"')):
            v = v[1:-1]
        out[k] = v
    return out or None

need = ["OKX_API_KEY","OKX_API_SECRET","OKX_API_PASSPHRASE","KRAKEN_API_KEY","KRAKEN_API_SECRET"]
merged = {}

# load from candidates
for p in CANDIDATES:
    d = load_candidate(p)
    if not d: continue
    for k in need:
        if k in d and d[k] and k not in merged:
            merged[k] = str(d[k])

# environment fallback (if user exported anything)
for k in need:
    if k not in merged or not merged[k]:
        v = os.environ.get(k)
        if v: merged[k] = v

# final structure (empty strings allowed but we keep keys)
final = {k: merged.get(k, "") for k in need}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(final, indent=2), encoding="utf-8")

def mask(x):
    x = str(x or "")
    return x if len(x)<=8 else x[:4]+"…"+x[-4:]
print(f"[ok] wrote -> {OUT}")
print("[mask preview]")
for k in sorted(final):
    print(f"  {k} = {mask(final[k])}")
