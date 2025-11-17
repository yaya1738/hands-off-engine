#!/usr/bin/env python3
import os, sys, urllib.parse, urllib.request, json

ENV = os.path.expanduser("~/hands-off/state/tg/bots/handsoff.env")
def read_env(path):
    d={}
    with open(path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v = line.split("=",1)
            d[k.strip()]=v.strip()
    return d

def send(msg):
    e = read_env(ENV)
    token = e.get("TOKEN")
    chat  = e.get("CHAT_ID")
    if not token or not chat:
        raise SystemExit("[err] Missing TOKEN or CHAT_ID in env file")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": msg,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        payload = json.loads(r.read().decode())
    if payload.get("ok") is True:
        print("[ok] Telegram sent")
    else:
        print("[err] Telegram API:", payload)
        raise SystemExit(1)

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv)>1 else "Ping"
    send(msg)
