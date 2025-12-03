import os, json, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser("~")
STATE = f"{HOME}/hands-off-out/state"
LOG = f"{STATE}/alerts_log.jsonl"

def send_tg(text):
    # reuse same Termux tg env
    d={}
    p=f"{HOME}/hands-off/state/tg/bots/handsoff.env"
    if os.path.exists(p):
        for line in open(p,encoding="utf-8",errors="ignore"):
            if "=" in line:
                k,v=line.split("=",1); d[k.strip()]=v.split("#",1)[0].strip().strip('"').strip("'")
    token=d.get("TOKEN") or d.get("BOT_TOKEN") or d.get("TG_TOKEN"); chat=d.get("CHAT_ID") or d.get("TG_CHAT_ID")
    if not token or not chat: return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    try: urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10); return True
    except: return False

def main():
    if not os.path.exists(LOG): return
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1, minutes=5)
    items=[]
    for line in open(LOG,encoding="utf-8"):
        try:
            o=json.loads(line)
            ts=datetime.fromisoformat(o["ts"].replace("Z","+00:00"))
            if ts>=cutoff: items.append((ts,o["msg"]))
        except: pass
    if not items: return
    items.sort()
    head=f"🧾 Finance — hourly recap ({len(items)} alert(s))"
    body="\n\n".join([m for _,m in items[-8:]])
    send_tg(head+"\n\n"+body)

if __name__=="__main__": main()
