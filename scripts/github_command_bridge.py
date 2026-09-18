#!/usr/bin/env python3
"""Fail-closed inbound GitHub control-command adapter for Node 1."""
import json, logging, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
BUS=ROOT/"ai/coordination/messages.jsonl"
STATE=ROOT/"state/github_command_bridge_state.json"
ISSUE=int(os.getenv("FACTORY_CONTROL_ISSUE","272"))
REPO=os.getenv("FACTORY_GITHUB_REPO","yaya1738/hands-off-engine")
ACTORS=frozenset(x.strip() for x in os.getenv("FACTORY_GITHUB_COMMAND_ACTORS","yaya1738").split(",") if x.strip())
ACTIONS=frozenset({"health_check","system_status","read_file_fact","list_backends","list_parties","bus_summary","test_status","lifecycle_summary"})
log=logging.getLogger("GitHubCommandBridge")

def _state():
    try: return json.loads(STATE.read_text())
    except Exception: return {"processed":[]}

def _save(s):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    s["processed"]=sorted(set(s.get("processed",[])))[-5000:]
    STATE.write_text(json.dumps(s,indent=2)+"\n")

def _comments():
    url=f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments?per_page=100&direction=desc"
    req=urllib.request.Request(url,headers={"Accept":"application/vnd.github+json","User-Agent":"hands-off-engine-node1"})
    with urllib.request.urlopen(req,timeout=10) as r: return json.loads(r.read())

def _parse(body):
    lines=[x.strip() for x in body.splitlines()]
    if "[factory-command]" not in lines: return None
    d={}
    for line in lines[lines.index("[factory-command]")+1:]:
        if "=" in line:
            k,v=line.split("=",1); d[k.strip()]=v.strip()
    if not d.get("idempotency_key") or not d.get("objective") or d.get("action") not in ACTIONS: return None
    params={}
    if d["action"]=="read_file_fact":
        if not d.get("file_path"): return None
        params={k:d[k] for k in ("file_path","fact") if d.get(k)}
    return d,params

def poll_once():
    s=_state(); done=set(map(str,s.get("processed",[]))); admitted=0
    for c in _comments():
        cid=str(c.get("id",""))
        if not cid or cid in done: continue
        done.add(cid)
        actor=((c.get("user") or {}).get("login") or "")
        parsed=_parse(c.get("body") or "")
        if actor not in ACTORS or parsed is None: continue
        d,params=parsed
        msg={"from":"factory","to":"anyclaw","type":"task_assignment","message":d["objective"][:240],"msg_id":f"github-command-{cid}","timestamp":datetime.now(timezone.utc).isoformat(),"context":{"task_id":f"github-{d['idempotency_key']}","action":d["action"],"params":params,"reply_to":f"github-issue-{ISSUE}-comment-{cid}","source":"github_issue","source_comment_id":cid,"idempotency_key":d["idempotency_key"],"execution_enabled":False}}
        BUS.parent.mkdir(parents=True,exist_ok=True)
        with BUS.open("a") as f: f.write(json.dumps(msg)+"\n")
        admitted+=1
    s["processed"]=list(done); s["last_poll"]=datetime.now(timezone.utc).isoformat(); _save(s)
    return admitted

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"admitted={poll_once()}")
