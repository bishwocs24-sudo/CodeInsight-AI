"""Bounded, non-executing snippet scanner for the Vercel deployment."""
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib" / "hosted_python"))
from static_analysis import analyze_static

MAX_CODE_BYTES = 24_000
MAX_REQUEST_BYTES = 6 * MAX_CODE_BYTES + 256
LANGUAGES = {"python", "javascript", "typescript", "c", "cpp"}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.headers.get_content_type() != "application/json":
            return self.reply(415, {"error": "Send an application/json request."})

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.reply(400, {"error": "Invalid request length."})
        if length < 1 or length > MAX_REQUEST_BYTES:
            return self.reply(413, {"error": "The request exceeds the scan limit or is empty."})

        try:
            data = json.loads(self.rfile.read(length))
            language = data.get("language") if isinstance(data, dict) else None
            code = data.get("code") if isinstance(data, dict) else None
            if not isinstance(language, str) or language not in LANGUAGES:
                return self.reply(400, {"error": "Choose a supported language."})
            if not isinstance(code, str) or not code.strip():
                return self.reply(400, {"error": "Enter source code to scan."})
            if len(code.encode("utf-8")) > MAX_CODE_BYTES:
                return self.reply(413, {"error": "Source code must be 24 KB or smaller."})
            result = analyze_static(language, code)
        except (ValueError, RecursionError):
            return self.reply(400, {"error": "The input could not be parsed."})
        result["findings"] = result["findings"][:200]
        return self.reply(200, result)

    def reply(self, status, data):
        body = json.dumps(data, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)
