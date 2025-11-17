import json, os, math, time
from pathlib import Path
STATE = Path.home()/ "hands-off"/"state"/"finance.json"
WEIGHTS = Path.home()/ "hands-off"/"state"/"weights.json"
DEFAULT_WEIGHTS = {"cash":0.34,"crypto":0.33,"polymarket":0.33}
ALPHA,DECAY=0.25,0.98
def load_json(p,d):
    try: return json.loads(Path(p).read_text())
    except: return d
def save_json(p,d):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(d,indent=2))
def rolling_scores(hist,now=None):
    now=now or time.time(); s={"cash":0,"crypto":0,"polymarket":0}
    for h in sorted(hist,key=lambda x:x.get("ts",now)):
        ts=h.get("ts",now); days=max(0,(now-ts)/86400); w=DECAY**days
        for k in s: s[k]+=w*float(h.get(f"{k}_pnl",0))
    return s
def softmax(d):
    m=max(d.values()) if d else 0; e={k:math.exp(v-m) for k,v in d.items()}
    z=sum(e.values()) or 1; return {k:e[k]/z for k in e}
def nudge(w,s):
    pref=softmax(s); out={}
    for k in ("cash","crypto","polymarket"):
        t=pref.get(k,1/3)
        out[k]=max(0,min(1,(1-ALPHA)*w.get(k,1/3)+ALPHA*t))
    s2=sum(out.values()) or 1
    for k in out: out[k]/=s2
    return out
def rec(b,w):
    tot=sum(max(0,b.get(x,0)) for x in ("cash_usd","crypto_usd","polymarket_usd"))
    if tot<=0:return {"cash":0,"crypto":0,"polymarket":0,"notes":"No capital"}
    return {k:round(tot*w[k],2) for k in w}
def main():
    st=load_json(STATE,{"balances":{"cash_usd":0,"crypto_usd":0,"polymarket_usd":0},"history":[]})
    w=load_json(WEIGHTS,DEFAULT_WEIGHTS)
    sc=rolling_scores(st.get("history",[]))
    w2=nudge(w,sc)
    r=rec(st.get("balances",{}),w2)
    out={"ts":int(time.time()),"weights_prev":w,"scores":sc,"weights":w2,"recommend":r}
    print(json.dumps(out,indent=2)); save_json(WEIGHTS,w2)
if __name__=="__main__": main()
