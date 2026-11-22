import json, os, getpass, sys
from pathlib import Path

PRIVATE_ROOT = Path(os.environ.get("HANDS_OFF_PRIVATE_DIR", str(Path.home()/".config"/"hands-off-engine"))).expanduser()
vault = PRIVATE_ROOT/"secrets"/"termux-agent-vault.json"
vault.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
vault.parent.chmod(0o700)
data = {}
if os.path.exists(vault):
    try:
        with open(vault,"r") as f: data = json.load(f)
    except: data = {}
def ask(k, hidden=False):
    cur = data.get(k, "")
    prompt = f"{k} [{'set' if cur else 'unset'}]: "
    try:
        v = getpass.getpass(prompt) if hidden else input(prompt)
    except EOFError:
        v = ""
    if v.strip():
        data[k] = v.strip()

print("-- Enter values to set/replace; press Enter to keep --")
# Add keys as we integrate sources; safe to skip now
for k, hidden in [
    ("OKX_API_KEY", False), ("OKX_API_SECRET", True), ("OKX_API_PASSPHRASE", False),
    ("KRAKEN_API_KEY", False), ("KRAKEN_API_SECRET", True),
    ("ETHERSCAN_API_KEY", False), ("POLYMARKET_JWT", True)
]:
    ask(k, hidden)

with open(vault,"w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
vault.chmod(0o600)
print("\n[ok] private vault updated")
