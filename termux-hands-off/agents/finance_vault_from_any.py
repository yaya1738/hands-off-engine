import os, json, pathlib, re, sys

HOME = pathlib.Path.home()
PRIVATE_ROOT = pathlib.Path(os.environ.get("HANDS_OFF_PRIVATE_DIR", str(HOME/".config"/"hands-off-engine"))).expanduser()
CREDENTIALS_DIR = PRIVATE_ROOT/"secrets"
CANDIDATES = [
    CREDENTIALS_DIR/"keys.vault",
    *sorted(CREDENTIALS_DIR.glob("keys.vault.bak.*"), reverse=True)
]
OUT = PRIVATE_ROOT/"secrets"/"vault.json"

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
existing = load_candidate(OUT) or {}
final = dict(existing)
added = []

for k in need:
    if final.get(k):
        continue
    value = None
    for candidate in CANDIDATES:
        data = load_candidate(candidate)
        if data and data.get(k):
            value = str(data[k])
            break
    if not value:
        value = os.environ.get(k)
    if value:
        final[k] = str(value)
        added.append(k)
    else:
        final.setdefault(k, "")

if not any(final.get(k) for k in need):
    print("[blocked] no exchange credentials found; no vault was created or overwritten")
    raise SystemExit(1)

PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
PRIVATE_ROOT.chmod(0o700)
OUT.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
OUT.parent.chmod(0o700)
if added or not OUT.exists():
    OUT.write_text(json.dumps(final, indent=2), encoding="utf-8")
OUT.chmod(0o600)

print(f"[ok] private vault available -> {OUT}")
print(f"Newly imported fields: {len(added)}")
for k in sorted(need):
    print(f"  {k}: {'configured' if final.get(k) else 'missing'}")
