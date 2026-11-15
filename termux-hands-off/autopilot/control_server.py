import os, json, subprocess, urllib.parse, hmac, math
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST, PORT = "0.0.0.0", 8765
TOKEN = os.environ.get("CONTROL_TOKEN", "")

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if not self._auth():
            return self._ok('unauthorized', 401)
        try:
            ln = int(self.headers.get("Content-Length", "0") or 0)
            if not 0 <= ln <= 16384:
                return self._ok("invalid request size", 413)
        except ValueError:
            return self._ok("invalid content length", 400)
        body = self.rfile.read(ln).decode("utf-8") if ln > 0 else ""
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
            try:
                p_fair = float(pf)
                p_mkt = float(pm)
                if not (math.isfinite(p_fair) and math.isfinite(p_mkt)):
                    raise ValueError("probabilities must be finite")
                if not (0 <= p_fair <= 1 and 0 <= p_mkt <= 1):
                    raise ValueError("probabilities must be between 0 and 1")
                if not isinstance(key, str) or not key or len(key) > 200:
                    raise ValueError("invalid candidate key")
                if not isinstance(note, str) or len(note) > 2000:
                    raise ValueError("invalid note")
            except (TypeError, ValueError) as exc:
                return self._ok(str(exc), 400)
            line = json.dumps({"key": key, "p_fair": p_fair, "p_mkt": p_mkt, "note": note}) + "\n"
            with open(os.path.expanduser('~/hands-off/autopilot/candidates.jsonl'),'a') as f:
                f.write(line)
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
        supplied = self.headers.get("X-Token", "")
        return bool(TOKEN) and bool(supplied) and hmac.compare_digest(supplied, TOKEN)

    def do_GET(self):
        if not self._auth():
            return self._ok("unauthorized", 401)
        path, _, qs = self.path.partition("?")
        q = dict(urllib.parse.parse_qsl(qs))

        if path == "/ping":
            return self._ok("pong")

        if path == "/run/notify_once":
            thr = q.get("v") or ""
            env = os.environ.copy()
            if thr:
                try:
                    value = float(thr)
                    if not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError
                except ValueError:
                    return self._ok("threshold must be a finite number between 0 and 1", 400)
                env["EDGE_THRESHOLD"] = str(value)
            cmd = [
                "bash", "-lc",
                'cd "$HOME/hands-off/autopilot" && source ../.venv/bin/activate && ./notify_once.sh'
            ]
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
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
            try:
                n = int(q.get("n", "120"))
                if not 1 <= n <= 500:
                    raise ValueError
            except ValueError:
                return self._ok("n must be an integer between 1 and 500", 400)
            log_path = os.path.expanduser(
                "~/hands-off/autopilot/edges-" + datetime.utcnow().strftime("%Y%m%d") + ".log"
            )
            r = subprocess.run(["tail", "-n", str(n), log_path], capture_output=True, text=True, timeout=10)
            return self._ok(r.stdout or r.stderr)

        if path == "/set/threshold":
            thr = q.get("v","0.05")
            return self._ok(f"Set EDGE_THRESHOLD to {thr} for next manual run. Use: EDGE_THRESHOLD={thr} ./notify_once.sh")

        return self._ok("not found", 404)

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("CONTROL_TOKEN must be configured; refusing to start unauthenticated")
    print(f"Listening on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
