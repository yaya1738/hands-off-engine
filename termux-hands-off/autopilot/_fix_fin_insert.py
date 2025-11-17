import io, os, re, sys
FN = os.path.expanduser('~/hands-off/autopilot/admin_server.py')
STATE = os.path.expanduser('~/hands-off/data/finances/state.json')

with io.open(FN, 'r', encoding='utf-8') as f:
    src = f.read()

# Remove any previous "finance networth + metrics v2" block
src = re.sub(
    r'\n[ \t]*# --- inserted finance networth \+ metrics v2 ---.*?#[ \t]*--- end inserted block ---\n',
    '\n', src, flags=re.S)

# Find do_GET body range
m = re.search(r'\n[ \t]*def[ \t]+do_GET\(self\):\n', src)
if not m:
    print('[patch] do_GET not found', file=sys.stderr); sys.exit(2)
start = m.end()

# Find the indentation of the do_GET body (assume next non-empty line)
m2 = re.search(r'\n([ \t]+)\S', src[start:])
indent = m2.group(1) if m2 else '        '  # default 8 spaces

# Find the LAST generic 404 inside do_GET (without a trailing write)
do_get_tail = src[start:]
candidates = list(re.finditer(r'\n'+re.escape(indent)+r'self\.send_response\(404\);[ \t]*self\.end_headers\(\)[ \t]*\n', do_get_tail))
if not candidates:
    print('[patch] generic 404 anchor not found inside do_GET', file=sys.stderr); sys.exit(2)
last404 = candidates[-1]
insert_pos = start + last404.start()

block = f'''
{indent}# --- inserted finance networth + metrics v2 ---
{indent}if self.path == "/finance/networth":
{indent}    tok = self.headers.get("X-Admin-Token","")
{indent}    if not tok:
{indent}        self.send_response(403); self.end_headers(); return
{indent}    import os, json
{indent}    try:
{indent}        with open(os.path.expanduser("{STATE}"), "r", encoding="utf-8") as f:
{indent}            st = json.load(f)
{indent}        bal = st.get("balances", {{}})
{indent}        total = 0.0
{indent}        items = []
{indent}        for k, v in bal.items():
{indent}            try:
{indent}                vv = float(v)
{indent}                total += vv
{indent}                items.append({{"key": k, "value": vv}})
{indent}            except Exception:
{indent}                pass
{indent}        out = {{"total": total, "items": items}}
{indent}        body = json.dumps(out).encode()
{indent}        self.send_response(200)
{indent}        self.send_header("Content-Type","application/json")
{indent}        self.end_headers()
{indent}        self.wfile.write(body)
{indent}    except FileNotFoundError:
{indent}        self.send_response(404); self.end_headers(); self.wfile.write(b"state.json not found\\n")
{indent}    except Exception as e:
{indent}        self.send_response(500); self.end_headers(); self.wfile.write(str(e).encode())
{indent}    return

{indent}if self.path == "/metrics":
{indent}    tok = self.headers.get("X-Admin-Token","")
{indent}    if not tok:
{indent}        self.send_response(403); self.end_headers(); return
{indent}    import os, json
{indent}    m = ["admin_up 1"]
{indent}    try:
{indent}        with open(os.path.expanduser("{STATE}"), "r", encoding="utf-8") as f:
{indent}            st = json.load(f)
{indent}        notes = st.get("notes", [])
{indent}        m.append("fin_notes_total %d" % (len(notes),))
{indent}        bal = st.get("balances", {{}})
{indent}        total = 0.0
{indent}        for k, v in bal.items():
{indent}            try:
{indent}                vv = float(v); total += vv
{indent}                m.append('balance{{asset="%s"}} %s' % (k, vv))
{indent}            except Exception:
{indent}                pass
{indent}        m.append("networth_total %s" % (total,))
{indent}    except Exception:
{indent}        m.append("fin_notes_total 0")
{indent}    body = ("\\n".join(m) + "\\n").encode()
{indent}    self.send_response(200)
{indent}    self.send_header("Content-Type","text/plain")
{indent}    self.end_headers()
{indent}    self.wfile.write(body)
{indent}    return
{indent}# --- end inserted block ---
'''

new_src = src[:insert_pos] + block + src[insert_pos:]

bak = FN + '.pre_fix_fin_insert'
with io.open(bak, 'w', encoding='utf-8') as f: f.write(src)
with io.open(FN, 'w', encoding='utf-8') as f: f.write(new_src)
print('[patch] applied; backup:', bak)
