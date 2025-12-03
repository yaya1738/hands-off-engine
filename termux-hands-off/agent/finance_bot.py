#!/data/data/com.termux/files/usr/bin/python
import os, time, json, requests, traceback, sys

BASE   = os.path.expanduser("~/hands-off")
STATE  = f"{BASE}/state"
AGENT  = f"{BASE}/agent"
LOGDIR = os.path.expanduser("~/.cron-logs")

TG_ENV = f"{STATE}/tg/bots/handsoff.env"   # TOKEN=... CHAT_ID=...
ENV_AS_DICT = {}

def load_env(path):
    d={}
    if os.path.exists(path):
        for line in open(path, 'r', encoding='utf-8'):
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v=line.split('=',1)
            d[k.strip()]=v.strip()
    return d

def money(x):
    try: return f"${float(x):,.2f}"
    except: return "-"

def read_json(path, default=None):
    try:
        if os.path.exists(path):
            return json.load(open(path, 'r', encoding='utf-8'))
    except: pass
    return default

def send_message(txt):
    tok = ENV_AS_DICT.get("TOKEN"); chat = ENV_AS_DICT.get("CHAT_ID")
    if not tok or not chat: return
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    try: requests.post(url, json={"chat_id": chat, "text": txt}, timeout=15)
    except: pass

def allowed(update):
    """Only accept messages from your configured CHAT_ID."""
    try:
        msg = update.get("message") or update.get("edited_message")
        if not msg: return False
        chat_id = str(msg.get("chat",{}).get("id",""))
        return chat_id == ENV_AS_DICT.get("CHAT_ID")
    except: return False

# Import the watcher logic so /status matches cron summaries
sys.path.insert(0, AGENT)
try:
    import finance_watcher as FW
except Exception as e:
    FW = None

HELP = (
    "🤖 Hands-Off bot commands:\n"
    "/help — this menu\n"
    "/status — recompute and send current net-worth summary\n"
    "/holdings — show tracked fiat & crypto inputs\n"
    "/pmlatest — last Polymarket compact presence + sizes\n"
    "/id — echo this chat id (debug)"
)

def cmd_status():
    if FW is None:
        return "Watcher module not found. Run the watcher once first."
    prev = read_json(f"{STATE}/finance_prev.json", {})
    curr = FW.calc_snapshot()
    delta = FW.diff(prev, curr)
    text  = FW.build_summary(curr, delta)
    # Persist latest snapshot so deltas remain consistent
    with open(f"{STATE}/finance_prev.json","w",encoding="utf-8") as f:
        json.dump(curr, f, indent=2)
    return text

def cmd_holdings():
    fiat = read_json(f"{STATE}/fiat_accounts.json", {})
    crypto = read_json(f"{STATE}/crypto_holdings.json", {})
    lines = ["💼 Holdings (inputs)"]
    if fiat:
        lines.append("Fiat:")
        for k,v in fiat.items():
            lines.append(f"- {k}: {money(v)}")
    else:
        lines.append("Fiat: (none configured)")
    if crypto:
        lines.append("\nCrypto amounts:")
        for cid,amt in crypto.items():
            lines.append(f"- {cid}: {amt}")
    else:
        lines.append("\nCrypto amounts: (none configured)")
    return "\n".join(lines)

def cmd_pmlatest():
    candidates = [
        f"{STATE}/polymarket-compact.json",
        f"{AGENT}/polymarket-compact.json",
        f"{STATE}/polymarket_compact.json"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                obj = read_json(p,{})
                cash = obj.get("cash_usd") or obj.get("cashUSD") or 0.0
                mark = obj.get("mark_value_usd") or obj.get("markUSD") or 0.0
                return f"🟣 Polymarket compact found:\n{p}\n- cash: {money(cash)}\n- mark: {money(mark)}"
            except:
                return f"Polymarket file present but parse failed: {p}"
    return "Polymarket compact not found."

def main():
    os.makedirs(LOGDIR, exist_ok=True)
    global ENV_AS_DICT
    ENV_AS_DICT = load_env(TG_ENV)
    tok = ENV_AS_DICT.get("TOKEN")
    chat = ENV_AS_DICT.get("CHAT_ID")
    if not tok or not chat:
        raise SystemExit("TOKEN/CHAT_ID missing in handsoff.env")

    offset = 0
    send_message("✅ Bot online. /help for commands.")
    while True:
        try:
            url = f"https://api.telegram.org/bot{tok}/getUpdates"
            r = requests.get(url, params={"timeout":50,"offset":offset+1}, timeout=60)
            r.raise_for_status()
            data = r.json()
            for upd in data.get("result", []):
                offset = upd["update_id"]
                if not allowed(upd): continue
                msg = upd.get("message") or upd.get("edited_message") or {}
                text = (msg.get("text") or "").strip()
                if not text: continue

                if text == "/help":
                    send_message(HELP)
                elif text == "/status":
                    send_message(cmd_status())
                elif text == "/holdings":
                    send_message(cmd_holdings())
                elif text == "/pmlatest":
                    send_message(cmd_pmlatest())
                elif text == "/id":
                    send_message(f"chat_id = {chat}")
                else:
                    send_message("Unknown command. Try /help")
        except Exception as e:
            with open(f"{LOGDIR}/finance_bot.log","a",encoding="utf-8") as f:
                f.write("[error] "+repr(e)+"\n"+traceback.format_exc()+"\n")
            time.sleep(5)  # brief backoff

if __name__ == "__main__":
    main()
