import io, os, sys

FN = os.path.expanduser("~/hands-off/autopilot/admin_server.py")
STATE = os.path.expanduser("~/hands-off/data/finances/state.json")

with io.open(FN, "r", encoding="utf-8") as f:
    src = f.read()

marker = "# --- inserted finance networth + metrics v2 ---"
if marker in src:
    print("[patch] already present; nothing to do")
    sys.exit(0)

anchor = "self.send_response(404); self.end_headers()"
idx = src.find(anchor)
if idx < 0:
    print("[patch] anchor not found; aborting", file=sys.stderr)
    sys.exit(2)

block = r'''
        # --- inserted finance networth + metrics v2 ---
        if self.path == "/finance/networth":
            tok = self.headers.get("X-Admin-Token","")
            if not tok:
                self.send_response(403); self.end_headers(); return
            import os, json
            try:
                with open(os.path.expanduser("__STATE__"), "r", encoding="utf-8") as f:
                    st = json.load(f)
                bal = st.get("balances", {})
                total = 0.0
                items = []
                for k, v in bal.items():
                    try:
                        vv = float(v)
                        total += vv
                        items.append({"key": k, "value": vv})
                    except Exception:
                        pass
                out = {"total": total, "items": items}
                body = json.dumps(out).encode()
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404); self.end_headers(); self.wfile.write(b"state.json not found\n")
            except Exception as e:
                self.send_response(500); self.end_headers(); self.wfile.write(str(e).encode())
            return

        if self.path == "/metrics":
            tok = self.headers.get("X-Admin-Token","")
            if not tok:
                self.send_response(403); self.end_headers(); return
            import os, json
            m = ["admin_up 1"]
            try:
                with open(os.path.expanduser("__STATE__"), "r", encoding="utf-8") as f:
                    st = json.load(f)
                notes = st.get("notes", [])
                m.append("fin_notes_total %d" % (len(notes),))
                bal = st.get("balances", {})
                total = 0.0
                for k, v in bal.items():
                    try:
                        vv = float(v)
                        total += vv
                        m.append('balance{asset="%s"} %s' % (k, vv))
                    except Exception:
                        pass
                m.append("networth_total %s" % (total,))
            except Exception:
                m.append("fin_notes_total 0")
            body = ("\n".join(m) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Type","text/plain")
            self.end_headers()
            self.wfile.write(body)
            return
        # --- end inserted block ---
'''.replace("__STATE__", STATE.replace("\\", "\\\\"))

new_src = src[:idx] + block + src[idx:]

bak = FN + ".pre_fin_blocks"
with io.open(bak, "w", encoding="utf-8") as f:
    f.write(src)
with io.open(FN, "w", encoding="utf-8") as f:
    f.write(new_src)

print("[patch] applied; backup:", bak)
