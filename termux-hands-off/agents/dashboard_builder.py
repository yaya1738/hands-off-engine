#!/usr/bin/env python3
import json, csv, pathlib, datetime

HOME = pathlib.Path.home()
OUT  = HOME/"hands-off"/"dashboard"/"index.html"

EXT       = HOME/"hands-off"/"agents"/"external_accounts.json"
CARDS     = HOME/"hands-off"/"agents"/"cards.json"
BAL_LOG   = HOME/"hands-off"/"logs"/"finance_balances.log"
DAILY_CSV = HOME/"hands-off"/"logs"/"finance_daily.csv"
PERF_CSV  = HOME/"hands-off"/"logs"/"performance_daily.csv"
PM_POS_CSV= HOME/"hands-off"/"logs"/"polymarket_positions.csv"
CRED_LOG  = HOME/"hands-off"/"logs"/"finance_credit.log"
CARDS_JSON= HOME/"hands-off"/"logs"/"cards_status.json"

def last_json_line(path):
    if not path.exists(): return None
    last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try: last = json.loads(line)
        except: pass
    return last

def read_csv_rows(path):
    if not path.exists(): return []
    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        return list(rdr)

def money(x):
    try: return f"${float(x):,.2f}"
    except: return "-"

now = datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

ext = {}
if EXT.exists():
    try: ext = json.loads(EXT.read_text())
    except: ext = {}

cards_file = {}
if CARDS_JSON.exists():
    try: cards_file = json.loads(CARDS_JSON.read_text())
    except: cards_file = {}

balances_last = last_json_line(BAL_LOG) or {}
credit_last   = last_json_line(CRED_LOG) or {}

daily_rows = read_csv_rows(DAILY_CSV)
perf_rows  = read_csv_rows(PERF_CSV)
pm_rows    = read_csv_rows(PM_POS_CSV)

# derive quicks
net_usd = balances_last.get("usd_total_raw", balances_last.get("usd_total"))
util = credit_last.get("total_utilization")
stmt_notes = " / ".join(credit_last.get("statement_notes", []) or [])

pm_mark = ext.get("polymarket_positions_mark")
pm_unr  = ext.get("polymarket_unrealized_est")
pm_cash = ext.get("polymarket_cash")
pm_cost = ext.get("polymarket_cost_basis", 0)

rent_ils = ext.get("rent_monthly_shekel")
rent_usd = ext.get("rent_monthly_usd")

# Daily table rows
daily_slice = daily_rows[-30:] if daily_rows else []
daily_html = []
for r in daily_slice:
    date = r.get("date","")
    usd  = r.get("usd_last", r.get("usd_median"))
    delta = r.get("delta_vs_prev")
    try:
        dflt = float(delta) if delta not in ("", None) else None
    except:
        dflt = None
    cls = "mut" if dflt is None else ("pos" if dflt >= 0 else "neg")
    delta_txt = "-" if dflt is None else money(dflt)
    daily_html.append(f"<tr><td>{date}</td><td>{money(usd)}</td><td class='{cls}'>{delta_txt}</td></tr>")
daily_html = "\n".join(daily_html)

# Polymarket positions
pm_slice = pm_rows[-100:] if pm_rows else []
pm_html = []
for r in pm_slice:
    pm_html.append(
        f"<tr><td>{r.get('market','')}</td><td>{r.get('outcome','')}</td>"
        f"<td>{r.get('quantity','')}</td><td>{r.get('price','')}</td><td>{money(r.get('value'))}</td></tr>"
    )
pm_html = "\n".join(pm_html)

# Performance rows
perf_slice = perf_rows[-30:] if perf_rows else []
perf_html = []
for r in perf_slice:
    date = r.get("date","")
    pm   = r.get("polymarket_pnl", 0)
    rb   = r.get("robinhood_pnl", 0)
    tot  = r.get("total_pnl", 0)
    notes= r.get("notes","")
    try: cls_pm  = "pos" if float(pm)  >= 0 else "neg"
    except: cls_pm = "mut"
    try: cls_rb  = "pos" if float(rb)  >= 0 else "neg"
    except: cls_rb = "mut"
    try: cls_tot = "pos" if float(tot) >= 0 else "neg"
    except: cls_tot = "mut"
    perf_html.append(
        f"<tr><td>{date}</td><td class='{cls_pm}'>{money(pm)}</td>"
        f"<td class='{cls_rb}'>{money(rb)}</td><td class='{cls_tot}'>{money(tot)}</td><td>{notes}</td></tr>"
    )
perf_html = "\n".join(perf_html)

# Card status table
cards_rows = (cards_file.get("cards") or [])
cards_html = []
for c in cards_rows:
    util_pct = f"{round(float(c.get('util',0))*100,1)}%"
    cls = "pos" if float(c.get('util',0)) < 0.45 else ("neg" if float(c.get('util',0)) >= 0.50 else "mut")
    flags = ", ".join(c.get("flags",[])) or "-"
    cards_html.append(
        f"<tr><td>{c.get('name','')}</td><td>{money(c.get('limit'))}</td>"
        f"<td>{money(c.get('balance'))}</td><td class='{cls}'>{util_pct}</td>"
        f"<td>{c.get('days_to_statement','')}</td><td>{c.get('statement_day','')}</td>"
        f"<td>{c.get('apr_pct','')}</td><td>{flags}</td></tr>"
    )
cards_html = "\n".join(cards_html)

html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Hands-Off Dashboard</title>
<meta http-equiv="refresh" content="3600">
<style>
  :root {{
    --bg:#0b0f14; --fg:#e7f0ff; --mut:#9cb1d1; --card:#131a22; --accent:#59f;
    --pos:#1db954; --neg:#ff5c5c;
  }}
  body {{ background:var(--bg); color:var(--fg); font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,"Helvetica Neue",Arial,sans-serif; margin:0; padding:24px; }}
  h1 {{ margin:0 0 16px; font-size:24px; }}
  .grid {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(260px,1fr)); gap:16px; }}
  .card {{ background:var(--card); border-radius:16px; padding:16px; box-shadow:0 2px 12px rgba(0,0,0,.2); }}
  .k {{ font-size:13px; color:var(--mut); }}
  .v {{ font-size:22px; font-weight:700; }}
  .row {{ display:flex; justify-content:space-between; align-items:center; margin:8px 0; }}
  table {{ width:100%; border-collapse:collapse; margin-top:8px; font-size:13px; }}
  th, td {{ padding:8px; border-bottom:1px solid #223; text-align:left; }}
  th {{ color:var(--mut); font-weight:600; }}
  .pos {{ color:var(--pos); }}
  .neg {{ color:var(--neg); }}
  .mut {{ color:var(--mut); }}
  small {{ color:var(--mut); }}
  .pill {{ background:#1b2430; padding:4px 8px; border-radius:999px; font-size:12px; color:var(--mut); }}
</style>
</head>
<body>
  <h1>Hands-Off Dashboard <span class="pill">{now}</span></h1>

  <div class="grid">
    <div class="card">
      <div class="k">Net worth (live)</div>
      <div class="v">{money(net_usd) if net_usd is not None else "-"}</div>
      <div class="k">Includes external accounts + crypto balances</div>
    </div>

    <div class="card">
      <div class="k">Total utilization</div>
      <div class="v">{(str(round(util*100,1))+'%') if util is not None else '-'}</div>
      <div class="k">Statement reminders</div>
      <div class="k">{stmt_notes or '-'}</div>
    </div>

    <div class="card">
      <div class="k">Polymarket</div>
      <div class="row"><span class="k">Mark (EV)</span><span class="v">{money(pm_mark) if pm_mark is not None else '-'}</span></div>
      <div class="row"><span class="k">Cash</span><span class="v">{money(pm_cash) if pm_cash is not None else '-'}</span></div>
      <div class="row"><span class="k">Unrealized</span><span class="v {'pos' if (pm_unr or 0)>=0 else 'neg'}">{money(pm_unr) if pm_unr is not None else '-'}</span></div>
      <small>Cost basis: {money(pm_cost)}</small>
    </div>

    <div class="card">
      <div class="k">Rent</div>
      <div class="row"><span class="k">₪ / mo</span><span class="v">{('₪'+str(rent_ils)) if rent_ils else '-'}</span></div>
      <div class="row"><span class="k">$ / mo</span><span class="v">{money(rent_usd) if rent_usd else '-'}</span></div>
      <small>Adjust in external_accounts.json</small>
    </div>
  </div>

  <div class="card" style="margin-top:16px;">
    <div class="k">Daily Net Worth</div>
    <table>
      <thead><tr><th>Date</th><th>USD</th><th>Δ vs prev</th></tr></thead>
      <tbody>
        {daily_html}
      </tbody>
    </table>
  </div>

  <div class="card" style="margin-top:16px;">
    <div class="k">Cards (limits, utilization, statement countdown)</div>
    <table>
      <thead>
        <tr><th>Card</th><th>Limit</th><th>Balance</th><th>Util%</th><th>Days→Stmt</th><th>Stmt day</th><th>APR%</th><th>Flags</th></tr>
      </thead>
      <tbody>
        {cards_html}
      </tbody>
    </table>
    <small>Edit with agents/cards_limits_fill.py</small>
  </div>

  <div class="grid" style="margin-top:16px;">
    <div class="card">
      <div class="k">Positions (Polymarket, latest pull)</div>
      <table>
        <thead><tr><th>Market</th><th>Outcome</th><th>Qty</th><th>Price</th><th>Value</th></tr></thead>
        <tbody>
          {pm_html}
        </tbody>
      </table>
      <small>Full history at logs/polymarket_positions.csv</small>
    </div>

    <div class="card">
      <div class="k">Performance (manual/assisted P&L)</div>
      <table>
        <thead><tr><th>Date</th><th>Polymarket</th><th>Robinhood</th><th>Total</th><th>Notes</th></tr></thead>
        <tbody>
          {perf_html}
        </tbody>
      </table>
      <small>Edit agents/perf_inputs.json then run perf_logger.py (or use quick_update.py)</small>
    </div>
  </div>

  <p class="mut" style="margin-top:16px;">Data sources: external_accounts.json, cards.json, finance_balances.log, finance_daily.csv, cards_status.json, polymarket_positions.csv, performance_daily.csv, finance_credit.log.</p>
</body>
</html>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"[ok] dashboard -> {OUT}")
