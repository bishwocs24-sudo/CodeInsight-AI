"""Exercise the public scanner using its production HTTP handler."""
import importlib.util
import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
FRONTEND = PROJECT / "frontend"
spec = importlib.util.spec_from_file_location("hosted_scan", FRONTEND / "api" / "scan.py")
assert spec and spec.loader
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


class HostedScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), scan.handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def post(self, payload, content_type="application/json"):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request("POST", "/api/scan", json.dumps(payload),
                               {"Content-Type": content_type})
            response = connection.getresponse()
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_bundled_analyzer_matches_backend(self):
        backend = PROJECT / "backend" / "app" / "services" / "static_analysis.py"
        hosted = FRONTEND / "lib" / "hosted_python" / "static_analysis.py"
        self.assertEqual(backend.read_bytes(), hosted.read_bytes())

    def test_returns_evidence(self):
        status, result = self.post({"language": "python", "code": "\ndef labels(xs=[]):\n    return xs\n"})
        self.assertEqual(status, 200)
        self.assertEqual(result["findings"][0]["rule_id"], "PY005")
        self.assertEqual(result["findings"][0]["line"], 2)
        self.assertEqual(result["findings"][0]["evidence"], "def labels(xs=[]):")

    def test_returns_syntax_diagnostic(self):
        status, result = self.post({"language": "python", "code": "def broken("})
        self.assertEqual(status, 200)
        self.assertIn("Python syntax error at line 1", result["errors"][0])

    def test_validates_request(self):
        self.assertEqual(self.post({"language": [], "code": "foo()"})[0], 400)
        self.assertEqual(self.post({"language": "c", "code": " "})[0], 400)
        self.assertEqual(self.post({"language": "c", "code": "é" * 12_001})[0], 413)
        self.assertEqual(self.post({}, "text/plain")[0], 415)

    def test_caps_results(self):
        status, result = self.post({"language": "c", "code": "gets(buffer);\n" * 250})
        self.assertEqual(status, 200)
        self.assertEqual(result["finding_count"], 250)
        self.assertEqual(len(result["findings"]), 200)
