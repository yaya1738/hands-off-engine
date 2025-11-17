import os, json, subprocess, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST, PORT = "0.0.0.0", 8765
TOKEN = os.environ.get("CONTROL_TOKEN", "")

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if not self._auth():
            return self._ok('unauthorized', 401)
        ln = int(self.headers.get('Content-Length','0') or 0)
        body = self.rfile.read(ln).decode() if ln>0 else ''
        import json, urllib.parse, os
        try:
            data = json.loads(body) if body and body.strip().startswith('{') else dict(urllib.parse.parse_qsl(body))
        except:
            data = dict(urllib.parse.parse_qsl(body))
        path = self.path
        if path.startswith('/candidates/add'):
            key = data.get('key'); pf=data.get('p_fair'); pm=data.get('p_mkt'); note=data.get('note','')
            if not (key and pf and pm):
                return self._ok('missing fields', 400)
            line = '{"key":"%s","p_fair":%s,"p_mkt":%s,"note":"%s"}\n' % (key, pf, pm, note)
            with open(os.path.expanduser('~/hands-off/autopilot/candidates.jsonl'),'a') as f: f.write(line)
            return self._ok('ok')
        return self._ok('not found', 404)

    def _ok(self, body, code=200, ctype="text/plain; charset=utf-8"):
        if isinstance(body, (bytes, bytearray)):
            b = body
        elif isinstance(body, str):
            b = body.encode()
        else:
            b = json.dumps(body).encode()
            ctype = "application/json; charset=utf-8"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(b)

    def _auth(self):
        return self.headers.get("X-Token","") == TOKEN

    def do_GET(self):
        if not self._auth():
            return self._ok("unauthorized", 401)
        path, _, qs = self.path.partition("?")
        q = dict(urllib.parse.parse_qsl(qs))

        if path == "/ping":
            return self._ok("pong")

        if path == "/run/notify_once":
            thr = q.get("v") or ""
            # Run under bash -lc so "source" works; pass EDGE_THRESHOLD if provided
            cmd = (
                'bash -lc \'cd "$HOME/hands-off/autopilot"; '
                'source ../.venv/bin/activate; '
                + (f'EDGE_THRESHOLD="{thr}" ' if thr else '')
                + './notify_once.sh\''
            )
            r = run(cmd)
            return self._ok(r.stdout or r.stderr, 200 if r.returncode==0 else 500)

        if path == "/run/restart_loop":
            cmd = (
                'export TMUX_TMPDIR="$PREFIX/var/run"; mkdir -p "$TMUX_TMPDIR"; '
                'tmux -L autopilot start-server; '
                '(tmux -L autopilot has-session -t autopilot || tmux -L autopilot new-session -d -s autopilot -c "$HOME/hands-off"); '
                '(tmux -L autopilot list-windows -t autopilot | grep -q "^0:" && tmux -L autopilot kill-window -t autopilot:0 || true); '
                'tmux -L autopilot new-window -t autopilot -n sniffer -c "$HOME/hands-off" "./run_loop.sh"'
            )
            r = run(cmd)
            return self._ok(r.stdout or r.stderr, 200 if r.returncode==0 else 500)

        if path == "/logs/tail":
            n = int(q.get("n","120"))
            r = run('cd "$HOME/hands-off/autopilot" && tail -n {} edges-$(date -u +%Y%m%d).log || true'.format(n))
            return self._ok(r.stdout or r.stderr)

        if path == "/set/threshold":
            thr = q.get("v","0.05")
            return self._ok(f"Set EDGE_THRESHOLD to {thr} for next manual run. Use: EDGE_THRESHOLD={thr} ./notify_once.sh")

        return self._ok("not found", 404)

if __name__ == "__main__":
    print(f"Listening on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
