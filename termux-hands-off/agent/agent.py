import os, json, yaml, math, time, hmac, hashlib, base64
from pathlib import Path
from datetime import datetime, timezone
from rich import print as rprint
from rich.table import Table
import requests

CONFIG="finance_sources.yaml"
PRIVATE_ROOT = Path(os.environ.get("HANDS_OFF_PRIVATE_DIR", str(Path.home()/".config"/"hands-off-engine"))).expanduser()
VAULT = PRIVATE_ROOT/"secrets"/"termux-agent-vault.json"

def money(x):
    try: return "${:,.2f}".format(float(x))
    except: return "-"

def load_yaml(p): return yaml.safe_load(open(p))
def read_manual(p): return yaml.safe_load(open(p))
def load_vault():
    if VAULT.exists():
        try: return json.loads(VAULT.read_text(encoding="utf-8"))
        except: return {}
    return {}

def _clean(s):
    if s is None: return ""
    # single-line, no CR/LF, trimmed
    return str(s).replace("\r"," ").replace("\n"," ").strip()

# -----------------  OKX  -----------------
def okx_fetch_balance(vault):
    key=_clean(vault.get("OKX_API_KEY"))
    sec=_clean(vault.get("OKX_API_SECRET"))
    passp=_clean(vault.get("OKX_API_PASSPHRASE"))
    if not (key and sec and passp):
        return 0.0,"[gray]no OKX keys"
    url_path="/api/v5/account/balance"
    url="https://www.okx.com"+url_path
    ts=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # ISO8601 with ms
    prehash=f"{ts}GET{url_path}"
    sign=base64.b64encode(hmac.new(sec.encode(),prehash.encode(),hashlib.sha256).digest()).decode()
    headers={
        "OK-ACCESS-KEY": key,
        "OK-ACCESS-SIGN": _clean(sign),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": passp,
        "Content-Type": "application/json"
    }
    try:
        r=requests.get(url,headers=headers,timeout=12)
        j=r.json()
        if j.get("code") not in (None,"0",""):  # OKX error style
            return 0.0, f"[red]OKX error {j.get('code')}: {j.get('msg')}"
        total=0.0
        for d in j.get("data",[]):
            for c in d.get("details",[]):
                # Use eqUsd if present; fallback sums are possible but eqUsd is best
                if "eqUsd" in c:
                    try: total+=float(c["eqUsd"])
                    except: pass
        return total,"ok"
    except Exception as e:
        return 0.0,f"[red]{e}"

# -----------------  Kraken  -----------------
def kraken_fetch_balance(vault):
    key=_clean(vault.get("KRAKEN_API_KEY"))
    sec=_clean(vault.get("KRAKEN_API_SECRET"))
    if not (key and sec): return 0.0,"[gray]no Kraken keys"
    url="https://api.kraken.com/0/private/Balance"
    nonce=str(int(time.time()*1000))
    data=f"nonce={nonce}".encode()
    path="/0/private/Balance"
    msg=(nonce+path).encode()+hashlib.sha256(data).digest()
    try:
        sec_b64=base64.b64decode(sec)
    except Exception:
        return 0.0,"[red]Kraken secret not base64?"
    sig=base64.b64encode(hmac.new(sec_b64,msg,hashlib.sha512).digest())
    headers={"API-Key":key,"API-Sign":sig}
    try:
        r=requests.post(url,headers=headers,data={"nonce":nonce},timeout=12)
        j=r.json()
        if j.get("error"):
            return 0.0,f"[red]Kraken error: {j.get('error')}"
        total=0.0
        for k,v in (j.get("result") or {}).items():
            if k in ("ZUSD","USDT","USDC"):
                try: total+=float(v)
                except: pass
        return total,"ok"
    except Exception as e:
        return 0.0,f"[red]{e}"

# -----------------  Core aggregation -----------------
def compute_totals(doc):
    c=sum((doc.get("cash")or{}).values())
    x=sum((doc.get("crypto")or{}).values())
    s=sum((doc.get("securities")or{}).values())
    l=sum((doc.get("liabilities")or{}).values())
    return {"cash":c,"crypto":x,"securities":s,"liabilities":l,"net":c+x+s-l}

def main():
    print("BLOCKED: legacy finance aggregator is retired.")
    print("It mixes manual data with zero-on-error exchange responses and cannot establish financial truth.")
    print("Use the governed finance.truth adapter and private finance hub instead.")
    return 1

if __name__=="__main__": raise SystemExit(main())
