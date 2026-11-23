#!/usr/bin/env python3
"""Local, read-mostly control room for Yair to observe and message the AI swarm.

Binds to localhost by default. It does not execute arbitrary commands and only
writes operator messages through CommHub. The AI-to-AI event bus remains the
source of truth.
"""
from __future__ import annotations

import argparse
import base64
import hmac
import ipaddress
import json
import os
import secrets
import stat
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"
TOKEN_PATH = ROOT / "state" / "control_room.token"


def load_or_create_control_room_token(path: Path = TOKEN_PATH) -> str:
    """Load a private local UI credential, creating it once with owner-only access."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError("Control Room token path must be a regular file")
        os.chmod(path, 0o600)
        token = path.read_text(encoding="utf-8").strip()
        if len(token) < 32:
            raise RuntimeError("Control Room token file is invalid; inspect it before replacing")
        return token
    except FileNotFoundError:
        token = secrets.token_urlsafe(32)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError:
            return load_or_create_control_room_token(path)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(token + "\n")
        return token


def authorization_valid(header: str, token: str) -> bool:
    """Validate HTTP Basic credentials without accepting alternate identities."""
    if not header or not token or not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return False
    return username == "operator" and hmac.compare_digest(password, token)

HTML = r'''<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Yair • AI Control Room</title>
<style>
body{margin:0;background:#0b1020;color:#e8edf7;font:15px system-ui,sans-serif}
header{padding:14px 16px;border-bottom:1px solid #26304a;position:sticky;top:0;background:#0b1020cc;backdrop-filter:blur(8px)}
h1{font-size:20px;margin:0 0 4px}.sub{color:#8e9ab3;font-size:12px}
main{max-width:1000px;margin:auto;padding:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:12px}
.card{background:#121a2c;border:1px solid #26304a;border-radius:10px;padding:10px}.label{color:#8e9ab3;font-size:11px;text-transform:uppercase}.value{font-size:18px;margin-top:4px}
.section{margin-top:12px}.section h2{font-size:14px;margin:0 0 7px;color:#b7c2d9}
#lifecycle{display:flex;flex-direction:column;gap:7px;max-height:28vh;overflow:auto}.task{background:#11182a;border:1px solid #26304a;border-radius:9px;padding:9px}.task .meta{color:#8190ad;font-size:11px}.task .state{margin-top:4px;white-space:pre-wrap;word-break:break-word}
#feed{display:flex;flex-direction:column;gap:7px;max-height:48vh;overflow:auto}.msg{background:#11182a;border:1px solid #26304a;border-radius:9px;padding:9px}.meta{color:#8190ad;font-size:11px}.body{white-space:pre-wrap;margin-top:4px;word-break:break-word}
form{display:flex;gap:8px;margin-top:12px;position:sticky;bottom:8px}input{flex:1;background:#11182a;color:#fff;border:1px solid #35415f;border-radius:9px;padding:12px}button{background:#e8edf7;color:#0b1020;border:0;border-radius:9px;padding:0 16px;font-weight:700}
</style></head><body><header><h1>Yair • AI Control Room</h1><div class="sub">Observe the swarm. Message the system. AI-to-AI traffic stays on the CommHub bus.</div></header>
<main><section class="grid"><div class="card"><div class="label">Bus</div><div id="bus" class="value">—</div></div><div class="card"><div class="label">Messages</div><div id="count" class="value">0</div></div><div class="card"><div class="label">AI parties</div><div id="parties" class="value">—</div></div><div class="card"><div class="label">Lifecycle tasks</div><div id="lifecycleCount" class="value">0</div></div><div class="card"><div class="label">Admitted reqs</div><div id="admitted" class="value">0</div></div><div class="card"><div class="label">Factory decisions</div><div id="decisions" class="value">0</div></div><div class="card"><div class="label">DASS heartbeat</div><div id="hb" class="value">—</div></div><div class="card"><div class="label">Last activity</div><div id="last" class="value">—</div></div></section>
<section class="section"><h2>Task lifecycle</h2><div id="lifecycle"></div></section>
<section class="section"><h2>Intake</h2><div class="grid"><div class="card"><div class="label">Request admissions</div><div id="admList" class="value">—</div></div><div class="card"><div class="label">Request rejections</div><div id="rejList" class="value">—</div></div><div class="card"><div class="label">Factory decisions</div><div id="decList" class="value">—</div></div></div></section>
<section class="section"><h2>Interaction threads</h2><div id="threads" class="value">—</div></section>
<section class="section"><h2>Canonical bus</h2><div id="feed"></div></section><form id="send"><input id="text" autocomplete="off" placeholder="Tell the AI system what to work on…"><button>Send</button></form></main>
<script>
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function refresh(){try{let r=await fetch('/api/state');let d=await r.json();let events=d.bus.events||[];document.querySelector('#bus').textContent=d.bus.available?'ONLINE':'WAITING';document.querySelector('#count').textContent=events.length;let ps=[...new Set(events.flatMap(x=>[x.from,x.to]).filter(Boolean))];document.querySelector('#parties').textContent=ps.length;document.querySelector('#last').textContent=events.length?new Date(events[events.length-1].timestamp).toLocaleTimeString():'—';let tasks=Object.entries(d.lifecycle.tasks||{});document.querySelector('#lifecycleCount').textContent=tasks.length;document.querySelector('#lifecycle').innerHTML=tasks.length?tasks.map(([id,x])=>{let current=x.current_state||x.status||'unknown';return `<article class="task"><div class="meta">${esc(id)} · ${esc(current)}</div><div class="state">${esc(JSON.stringify(x,null,2))}</div></article>`}).join(''):'<div class="meta">No lifecycle projection available.</div>';document.querySelector('#feed').innerHTML=events.slice().reverse().map(x=>`<article class="msg"><div class="meta">${esc(x.timestamp)} · ${esc(x.from)} → ${esc(x.to)} · ${esc(x.type)}</div><div class="body">${esc(JSON.stringify(x.payload??x.message??x,null,2))}</div></article>`).join('');let req=d.intake?.request||{},fac=d.intake?.factory||{};document.querySelector('#threads').innerHTML=(Array.isArray(d.threads)?d.threads:[]).map(t=>`<article class='task'><div class='meta'>${esc(t.correlation_key)} · ${t.events.length} events · ${esc(t.correlation_quality)} · state:${esc(t.lifecycle_state||'unknown')}</div><div class='state'>${t.events.map(e=>`<div class='meta'>${esc(e.timestamp)} · ${esc(e.type)} · ${esc(e.msg_id||'unknown')} · ${esc(e.correlation_quality||'')}</div>`).join('')}</div></article>`).join('')||'<div class="meta">No threads.</div>';document.querySelector('#admitted').textContent=req.admitted_count??'—';document.querySelector('#decisions').textContent=fac.decision_count??'—';let hb=d.heartbeat||{};document.querySelector('#hb').textContent=hb.available?(hb.status||'running'):'—';document.querySelector('#admList').innerHTML=(req.admissions||[]).slice().reverse().map(x=>`<div class="meta">${esc(x.msg_id)} · ${esc(x.request_type||'')}</div>`).join('')||'<div class="meta">—</div>';document.querySelector('#rejList').innerHTML=(req.rejections||[]).slice().reverse().map(x=>`<div class="meta">${esc(x.msg_id)} · ${esc(x.reason||'')}</div>`).join('')||'<div class="meta">—</div>';document.querySelector('#decList').innerHTML=(fac.decisions||[]).slice().reverse().map(x=>`<div class="meta">${esc(x.event_id||x.fingerprint)} · ${esc(x.event_type||'')}${x.assigned_msg_id?' → '+esc(x.assigned_msg_id):''}</div>`).join('')||'<div class="meta">—</div>'}catch(e){document.querySelector('#bus').textContent='ERROR'}}
document.querySelector('#send').onsubmit=async e=>{e.preventDefault();let i=document.querySelector('#text'),text=i.value.trim();if(!text)return;let r=await fetch('/api/send',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({message:text})});let d=await r.json();if(!r.ok)alert(d.error||'send failed');else{i.value='';refresh()}};refresh();setInterval(refresh,1500);
</script></body></html>'''


MAX_REQUEST_BYTES = 8192

def is_loopback_host(host):
    """The control room is intentionally local-only; reject wildcard/LAN binds."""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def read_json_request(headers, stream):
    """Read a bounded JSON object and return (status, body, error)."""
    if headers.get("transfer-encoding"):
        return 400, None, "transfer-encoding is not supported"
    raw_length = headers.get("content-length")
    try:
        length = int(raw_length)
    except (TypeError, ValueError):
        return 400, None, "valid content-length required"
    if length < 0:
        return 400, None, "invalid content-length"
    if length > MAX_REQUEST_BYTES:
        return 413, None, "request body too large"
    try:
        body = json.loads(stream.read(length))
    except Exception:
        return 400, None, "invalid json"
    if not isinstance(body, dict):
        return 400, None, "json object required"
    return 200, body, None


def read_events(limit: int = 120):
    if not BUS.exists():
        return []
    lines = BUS.read_text(errors="replace").splitlines()[-limit:]
    out=[]
    for line in lines:
        try: out.append(json.loads(line))
        except json.JSONDecodeError: continue
    return out

class Handler(BaseHTTPRequestHandler):
    control_room_token = None

    def log_message(self, *_): pass

    def require_auth(self):
        if authorization_valid(self.headers.get("Authorization", ""), self.control_room_token or ""):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Hands-Off Control Room", charset="UTF-8"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def send_json(self, code, data):
        raw=json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if not self.require_auth():
            return
        path=urlparse(self.path).path
        if path=='/':
            raw=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if path=='/api/events':
            events=read_events(); self.send_json(200,{'available':BUS.exists(),'events':events}); return
        if path=='/api/state':
            try:
                sys.path.insert(0,str(ROOT)); from scripts.control_room_state import build_snapshot
                snapshot=build_snapshot(ROOT, bus_limit=120, lifecycle_limit=100)
                self.send_json(200,snapshot); return
            except Exception as e:
                self.send_json(500,{'error':str(e)}); return
        self.send_json(404,{'error':'not found'})
    def do_POST(self):
        if not self.require_auth():
            return
        if urlparse(self.path).path!='/api/send': self.send_json(404,{'error':'not found'}); return
        code, body, error = read_json_request(self.headers, self.rfile)
        if error:
            self.send_json(code, {'error': error}); return
        text=str(body.get('message','')).strip()
        if not text or len(text)>4000: self.send_json(400,{'error':'message must be 1-4000 characters'}); return
        try:
            sys.path.insert(0,str(ROOT)); from scripts.comm_hub import CommHub
            result=CommHub(repo_root=ROOT).receive('operator','inbound_from_operator',{'message':text,'source':'yair_control_room','timestamp':datetime.now(timezone.utc).isoformat()},channel='webhook')
            self.send_json(200,{'status':'sent','result':result})
        except Exception as e: self.send_json(500,{'error':str(e)})

def main():
    p=argparse.ArgumentParser(); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8787); a=p.parse_args()
    if not is_loopback_host(a.host):
        p.error("Control Room must bind to localhost/loopback only")
    token = load_or_create_control_room_token()
    Handler.control_room_token = token
    print(f'Yair Control Room: http://{a.host}:{a.port}')
    print(f'Control Room credential: username=operator; token stored at {TOKEN_PATH}')
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()

if __name__=='__main__': main()