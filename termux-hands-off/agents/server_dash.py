#!/usr/bin/env python3
import http.server, socketserver, pathlib, os

HOME = pathlib.Path.home()
ROOT = HOME/"hands-off"/"dashboard"
PORT = 8123

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve from ROOT regardless of cwd
        path = super().translate_path(path)
        # forcibly map to ROOT
        rel = os.path.relpath(path, os.getcwd())
        return os.path.join(ROOT, rel if rel != "." else "index.html")

if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"[ok] serving {ROOT} at http://127.0.0.1:{PORT}")
        try: httpd.serve_forever()
        except KeyboardInterrupt: pass
