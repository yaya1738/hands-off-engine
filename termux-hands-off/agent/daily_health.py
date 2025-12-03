#!/data/data/com.termux/files/usr/bin/python
import os, time, json, urllib.parse, urllib.request, subprocess

HOME = os.path.expanduser("~")
ENVF = os.path.join(HOME, "hands-off", "state", "tg", "bots", "handsoff.env")

def load_env(p):
    d={}
    try:
        for line in open(p, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k,v=line.strip().split("=",1)
                d[k]=v
    except FileNotFoundError:
        pass
    return d

def file_tail(path, n=5):
    try:
        out = subprocess.check_output(["tail","-n",str(n),path], stderr=subprocess.DEVNULL).decode("utf-8","ignore")
        return out.strip()
    except Exception:
        return "(no log)"

def tg_send(token, chat_id, text):
    url=f"https://api.telegram.org/bot{token}/sendMessage"
    data=urllib.parse.urlencode({"chat_id":chat_id,"text":text,"parse_mode":"HTML"}).encode()
    with urllib.request.urlopen(urllib.request.Request(url,data=data), timeout=20) as r:
        return r.read().decode("utf-8","ignore")

env = load_env(ENVF)
TOKEN = env.get("TOKEN","").strip()
CHAT_ID = env.get("CHAT_ID","").strip()
if not TOKEN or not CHAT_ID:
    raise SystemExit("Missing TOKEN/CHAT_ID")

ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
# Basic system stats
try:
    uptime = subprocess.check_output(["uptime","-p"]).decode().strip()
except Exception:
    uptime = "(uptime n/a)"
try:
    df = subprocess.check_output(["df","-h","/data/data/com.termux/files/home"]).decode().splitlines()
    disk = df[1] if len(df)>1 else "(disk n/a)"
except Exception:
    disk = "(disk n/a)"

fetch_tail = file_tail(os.path.join(HOME,".cron-logs","fetcher.log"), 6)
push_tail  = file_tail(os.path.join(HOME,".cron-logs","pm_push.log"), 6)
cron_tail  = file_tail(os.path.join(HOME,".cron-logs","cron.log"), 6)

msg = f"""🩺 <b>Daily Health</b> — {ts}
• Uptime: {uptime}
• Disk: {disk}
• fetcher.log (tail):
<code>{fetch_tail}</code>

• pm_push.log (tail):
<code>{push_tail}</code>

• cron.log (tail):
<code>{cron_tail}</code>
"""
print(tg_send(TOKEN, CHAT_ID, msg))
