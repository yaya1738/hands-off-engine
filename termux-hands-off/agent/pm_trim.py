#!/data/data/com.termux/files/usr/bin/python
import os, json, sys, pathlib, time, datetime

BASE=os.path.expanduser("~/hands-off")
OUT =os.path.join(BASE,"out")
SRC=os.path.join(OUT,"fetch-latest.json")
DST=os.path.join(OUT,"polymarket-compact.json")

def money(x): 
    return None if x is None else round(float(x),3)

def main():
    try:
        data=json.load(open(SRC,"r",encoding="utf-8"))
    except Exception as e:
        print(f"[err] read {SRC}: {e}", file=sys.stderr); sys.exit(1)
    pm=(data.get("providers",{}).get("polymarket",{}) or {})
    rows=(pm.get("data") or [])
    # active-only, has some price
    keep=[]
    seen=set()
    for r in rows:
        if r.get("active") is False or r.get("closed") is True: 
            continue
        price = r.get("bestBid")
        if price is None: price = r.get("lastTradePrice")
        if price is None: 
            continue
        slug=r.get("slug") or r.get("id") or r.get("question")
        if slug in seen: 
            continue
        seen.add(slug)
        keep.append({
            "query": r.get("query"),
            "slug": r.get("slug"),
            "question": r.get("question"),
            "bestBid": money(r.get("bestBid")),
            "last":   money(r.get("lastTradePrice")),
            "endDate": r.get("endDate")
        })
    # group by query, take top N per query by last/bestBid desc
    out={}
    for k in {x.get("query") for x in keep}:
        grp=[x for x in keep if x.get("query")==k]
        grp.sort(key=lambda z: (z["bestBid"] or z["last"] or 0), reverse=True)
        out[k]=grp[:12]  # cap per query
    compact={
        "timestamp": data.get("timestamp"),
        "counts": {k: len(v) for k,v in out.items()},
        "queries": sorted(out.keys()),
        "markets": out
    }
    pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)
    with open(DST,"w",encoding="utf-8") as f:
        json.dump(compact, f, indent=2, ensure_ascii=False)
    print(f"[ok] wrote {DST}")
if __name__=="__main__":
    main()
