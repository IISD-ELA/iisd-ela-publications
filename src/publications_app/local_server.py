import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .handler import handler


REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = REPO_ROOT / "static"


class LocalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") or parsed.path == "/health":
            self._serve_api(parsed)
            return
        self._serve_static(parsed.path)

    def do_OPTIONS(self):
        self._serve_api(urlparse(self.path))

    def _serve_api(self, parsed):
        response = handler(
            {
                "rawPath": parsed.path,
                "rawQueryString": parsed.query,
                "requestContext": {"http": {"method": self.command}},
            },
            None,
        )
        self.send_response(response["statusCode"])
        for key, value in response.get("headers", {}).items():
            self.send_header(key, value)
        self.end_headers()
        body = response.get("body", "")
        if body:
            self.wfile.write(body.encode("utf-8"))

    def _serve_static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        target = (STATIC_ROOT / path.lstrip("/")).resolve()
        if STATIC_ROOT not in target.parents and target != STATIC_ROOT:
            self.send_error(404)
            return
        if not target.exists() or not target.is_file():
            target = STATIC_ROOT / "index.html"
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(target.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), LocalHandler)
    print(f"Serving publications search on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
