import os, json, yaml, math, time, hmac, hashlib, base64
from datetime import datetime, timezone
from rich import print as rprint
from rich.table import Table
import requests

CONFIG="finance_sources.yaml"; VAULT="vault.json"

def money(x):
    try: return "${:,.2f}".format(float(x))
    except: return "-"

def load_yaml(p): return yaml.safe_load(open(p))
def read_manual(p): return yaml.safe_load(open(p))
def load_vault():
    if os.path.exists(VAULT):
        try: return json.load(open(VAULT))
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
    cfg=load_yaml(CONFIG); vault=load_vault()
    total={"cash":0,"crypto":0,"securities":0,"liabilities":0,"net":0}
    notes=[]; breakdown=[]
    for src in cfg.get("sources",[]):
        t=src["type"]
        if t=="manual_file":
            d=read_manual(src["path"]); s=compute_totals(d)
            for k in total: total[k]+=s[k]
            breakdown.append(("Manual",s["cash"],s["crypto"],s["securities"],s["liabilities"],s["net"]))
        elif t=="onchain_usdc_eth":
            # (kept but not used yet until you add ETHERSCAN + addresses)
            pass
        elif t=="okx_spot":
            val,msg=okx_fetch_balance(vault)
            total["crypto"]+=val
            breakdown.append(("OKX",0.0,val,0.0,0.0,val))
            notes.append(f"OKX status: {msg}")
        elif t=="kraken_spot":
            val,msg=kraken_fetch_balance(vault)
            total["crypto"]+=val
            breakdown.append(("Kraken",0.0,val,0.0,0.0,val))
            notes.append(f"Kraken status: {msg}")
    assets=total["cash"]+total["crypto"]+total["securities"]
    util=(total["liabilities"]/assets) if assets>0 else 0
    tbl=Table(title=f"Hands-Off Snapshot @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    tbl.add_column("Metric",style="cyan"); tbl.add_column("Value",style="green")
    for k,v in [("Cash",total["cash"]),("Crypto",total["crypto"]),("Securities",total["securities"]),
                ("Liabilities",f"({money(total['liabilities'])})"),("—","—"),
                ("Net Worth",total["net"]),("Utilization (est.)",f"{util*100:.1f}%")]:
        tbl.add_row(k,money(v) if not isinstance(v,str) else v)
    rprint(tbl)
    b=Table(title="Source Breakdown")
    for c in ["Source","Cash","Crypto","Securities","Liabilities","Net Add"]: b.add_column(c)
    for n,c,x,s,l,net in breakdown: b.add_row(n,money(c),money(x),money(s),money(l),money(net))
    rprint(b)
    if notes:
        rprint("[yellow]Notes:[/yellow]")
        for n in notes: rprint(f"- {n}")

if __name__=="__main__": main()
