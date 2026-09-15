#!/usr/bin/env python3
"""Local, read-mostly control room for Yair to observe and message the AI swarm."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "ai" / "coordination" / "messages.jsonl"

HTML = r'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Yair • AI Control Room</title><style>
body{margin:0;background:#0b1020;color:#e8edf7;font:15px system-ui,sans-serif}header{padding:14px 16px;border-bottom:1px solid #26304a;position:sticky;top:0;background:#0b1020ee;backdrop-filter:blur(8px)}h1{font-size:20px;margin:0 0 4px}.sub{color:#8e9ab3;font-size:12px}main{max-width:1000px;margin:auto;padding:12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-bottom:12px}.card,.msg,.task,.interaction{background:#11182a;border:1px solid #26304a;border-radius:10px;padding:9px}.card{background:#121a2c}.label{color:#8e9ab3;font-size:11px;text-transform:uppercase}.value{font-size:18px;margin-top:4px}.section{margin-top:12px}.section h2{font-size:14px;margin:0 0 7px;color:#b7c2d9}#lifecycle,#feed,#interactions{display:flex;flex-direction:column;gap:7px;max-height:30vh;overflow:auto}.meta{color:#8190ad;font-size:11px}.body,.state{white-space:pre-wrap;margin-top:4px;word-break:break-word}.corr{font-family:ui-monospace,monospace;font-size:11px;color:#9fb3d8;margin-top:4px}form{display:flex;gap:8px;margin-top:12px;position:sticky;bottom:8px}input{flex:1;background:#11182a;color:#fff;border:1px solid #35415f;border-radius:9px;padding:12px}button{background:#e8edf7;color:#0b1020;border:0;border-radius:9px;padding:0 16px;font-weight:700}
</style></head><body><header><h1>Yair • AI Control Room</h1><div class="sub">Shared observation surface for humans and agents. CommHub remains the canonical transport.</div></header><main><section class="grid"><div class="card"><div class="label">Bus</div><div id="bus" class="value">—</div></div><div class="card"><div class="label">Messages</div><div id="count" class="value">0</div></div><div class="card"><div class="label">AI parties</div><div id="parties" class="value">—</div></div><div class="card"><div class="label">Lifecycle</div><div id="lifecycleCount" class="value">0</div></div><div class="card"><div class="label">Heartbeat</div><div id="heartbeat" class="value">—</div></div></section>
<section class="section"><h2>Interaction correlation</h2><div id="interactions"></div></section><section class="section"><h2>Task lifecycle</h2><div id="lifecycle"></div></section><section class="section"><h2>Canonical bus</h2><div id="feed"></div></section><form id="send"><input id="text" autocomplete="off" placeholder="Tell the AI system what to work on…"><button>Send</button></form></main>
<script>
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function corr(x){let p=x&&typeof x.payload==='object'&&x.payload?x.payload:{};let c=p&&typeof p.context==='object'&&p.context?p.context:{};return {msg_id:x.id||x.msg_id,task_id:c.task_id||p.task_id||x.task_id,reply_to:p.reply_to||x.reply_to,type:x.type,timestamp:x.timestamp}};
async function refresh(){try{let r=await fetch('/api/state');let d=await r.json();let events=d.bus.events||[];document.querySelector('#bus').textContent=d.bus.available?'ONLINE':'WAITING';document.querySelector('#count').textContent=events.length;document.querySelector('#parties').textContent=[...new Set(events.flatMap(x=>[x.from,x.to]).filter(Boolean))].length;let hb=d.heartbeat||{};document.querySelector('#heartbeat').textContent=hb.available?(hb.fail_closed?'FAIL-CLOSED':'UNKNOWN'):'WAITING';let tasks=Object.entries(d.lifecycle.tasks||{});document.querySelector('#lifecycleCount').textContent=tasks.length;document.querySelector('#lifecycle').innerHTML=tasks.length?tasks.map(([id,x])=>`<article class="task"><div class="meta">${esc(id)} · ${esc(x.current_state||x.status||'unknown')}</div><div class="state">${esc(JSON.stringify(x,null,2))}</div></article>`).join(''):'<div class="meta">No lifecycle projection available.</div>';let cs=events.slice().reverse().map(corr);let seen=new Set();let unique=cs.filter(x=>{let k=x.task_id||x.reply_to||x.msg_id;if(!k||seen.has(k))return false;seen.add(k);return true}).slice(0,30);document.querySelector('#interactions').innerHTML=unique.length?unique.map(x=>`<article class="interaction"><div class="meta">${esc(x.type)} · ${esc(x.timestamp)}</div><div class="corr">msg_id=${esc(x.msg_id)||'—'} · task_id=${esc(x.task_id)||'—'} · reply_to=${esc(x.reply_to)||'—'}</div></article>`).join(''):'<div class="meta">No correlated interactions available.</div>';document.querySelector('#feed').innerHTML=events.slice().reverse().map(x=>`<article class="msg"><div class="meta">${esc(x.timestamp)} · ${esc(x.from)} → ${esc(x.to)} · ${esc(x.type)}</div><div class="corr">msg_id=${esc(corr(x).msg_id)||'—'} · task_id=${esc(corr(x).task_id)||'—'} · reply_to=${esc(corr(x).reply_to)||'—'}</div><div class="body">${esc(JSON.stringify(x.payload??x.message??x,null,2))}</div></article>`).join('')}catch(e){document.querySelector('#bus').textContent='ERROR'}}
document.querySelector('#send').onsubmit=async e=>{e.preventDefault();let i=document.querySelector('#text'),text=i.value.trim();if(!text)return;let r=await fetch('/api/send',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({message:text})});let d=await r.json();if(!r.ok)alert(d.error||'send failed');else{i.value='';refresh()}};refresh();setInterval(refresh,1500);
</script></body></html>'''

def read_events(limit:int=120):
    if not BUS.exists(): return []
    lines=BUS.read_text(errors="replace").splitlines()[-limit:]; out=[]
    for line in lines:
        try: out.append(json.loads(line))
        except json.JSONDecodeError: continue
    return out

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*_): pass
    def send_json(self,code,data):
        raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/':
            raw=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if path=='/api/state':
            try:
                sys.path.insert(0,str(ROOT)); from scripts.control_room_state import build_snapshot
                self.send_json(200,build_snapshot(ROOT,bus_limit=120,lifecycle_limit=100,intake_limit=20)); return
            except Exception as e: self.send_json(500,{'error':str(e)}); return
        if path=='/api/events': self.send_json(200,{'available':BUS.exists(),'events':read_events()}); return
        self.send_json(404,{'error':'not found'})
    def do_POST(self):
        if urlparse(self.path).path!='/api/send': self.send_json(404,{'error':'not found'}); return
        try: body=json.loads(self.rfile.read(int(self.headers.get('content-length','0'))))
        except Exception: self.send_json(400,{'error':'invalid json'}); return
        text=str(body.get('message','')).strip()
        if not text or len(text)>4000: self.send_json(400,{'error':'message must be 1-4000 characters'}); return
        try:
            sys.path.insert(0,str(ROOT)); from scripts.comm_hub import CommHub
            result=CommHub(repo_root=ROOT).receive('operator','inbound_from_operator',{'message':text,'source':'yair_control_room','timestamp':datetime.now(timezone.utc).isoformat()},channel='webhook'); self.send_json(200,{'status':'sent','result':result})
        except Exception as e: self.send_json(500,{'error':str(e)})

def main():
    p=argparse.ArgumentParser(); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8787); a=p.parse_args(); print(f'Yair Control Room: http://{a.host}:{a.port}'); ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=='__main__': main()
