#!/usr/bin/env python3
"""Local receiver for the Perchance scene backend. A browser tab driving
https://perchance.org/ai-text-to-image-generator POSTs each rendered image
here; this crops it to 16:9, resizes to 1024x576 and saves it as PNG.

    python3 scripts/perchance_receiver.py <out_dir> [port]
POST /save?name=scene_0001.png   body: data URL or base64 of the image
"""
import base64, io, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from PIL import Image

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765


def to_16x9(img):
    img = img.convert("RGB"); w, h = img.size
    th = int(w * 9 / 16)
    if th <= h:
        top = (h - th) // 2; img = img.crop((0, top, w, top + th))
    else:
        tw = int(h * 16 / 9); left = (w - tw) // 2; img = img.crop((left, 0, left + tw, h))
    return img.resize((1024, 576), Image.LANCZOS)


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        if self.path.startswith("/items"):
            self.send_response(200); self._cors(); self.end_headers()
            self.wfile.write((OUT.parent / "perchance_items.json").read_bytes()); return
        self.send_response(200); self._cors(); self.end_headers()
        self.wfile.write(("\n".join(sorted(p.name for p in OUT.glob("*.png")))).encode())

    def do_POST(self):
        q = parse_qs(urlparse(self.path).query); name = Path(q["name"][0]).name
        raw = self.rfile.read(int(self.headers["Content-Length"])).decode()
        data = base64.b64decode(raw.split(",", 1)[-1])
        to_16x9(Image.open(io.BytesIO(data))).save(OUT / name)
        print("saved", name, flush=True)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a): pass


HTTPServer(("127.0.0.1", PORT), H).serve_forever()
