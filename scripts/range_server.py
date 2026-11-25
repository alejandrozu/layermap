"""Static file server with HTTP Range support (for testing the satellite pack loader)."""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


BLOBS = {}  # /_blob/<id> -> local pack file (to mimic artifact assets)
if os.path.exists('/home/claude/build/s2assets.json'):
    import json
    BLOBS = {u: '/home/claude/build/s2assets/' + n for n, u in json.load(open('/home/claude/build/s2assets.json')).items()}
NORANGE = os.environ.get('NORANGE') == '1'


class H(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        q = path.split('?')[0]
        if q in BLOBS: return BLOBS[q]
        return super().translate_path(path)

    def send_head(self):
        if NORANGE: return super().send_head()
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path): return super().send_head()
        m = re.match(r'bytes=(\d+)-(\d*)', rng)
        if not m: return super().send_head()
        size = os.path.getsize(path); a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
        b = min(b, size - 1)
        f = open(path, 'rb'); f.seek(a)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
        self.send_header('Content-Length', str(b - a + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        self.range_left = b - a + 1
        return f

    def copyfile(self, src, dst):
        n = getattr(self, 'range_left', None)
        if n is None: return super().copyfile(src, dst)
        while n > 0:
            buf = src.read(min(65536, n))
            if not buf: break
            dst.write(buf); n -= len(buf)

    def log_message(self, *a): pass


if __name__ == '__main__':
    os.chdir(sys.argv[1]); ThreadingHTTPServer(('', int(sys.argv[2])), H).serve_forever()
