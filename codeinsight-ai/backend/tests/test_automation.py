import hashlib
import hmac
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routes import automation
from app.core.config import get_settings
from app.main import app
from app.models.automation import ReviewJob
from app.platform_review import jobs
from app.platform_review.evidence import Source, added_lines, validate_ai
from app.platform_review.github_app import GitHubApp, StaleReview
from app.platform_review.pipeline import ai_review
from app.platform_review.sandbox import verify_python
from app.platform_review.scanner import scan


class EvidenceTests(unittest.TestCase):
    def test_diff_right_side_mapping(self):
        diff = "@@ -2,3 +2,3 @@\n context\n-old\n+new\n tail\n@@ -10,0 +11 @@\n++literal\n"
        self.assertEqual(added_lines(diff), {3: "new", 11: "+literal"})

    def test_model_output_requires_exact_path_line_quote_and_valid_schema(self):
        source = Source("main.py", "old\n  corrected", {2: "  corrected"})
        valid = {"path": "main.py", "line": 2, "quote": "  corrected",
                 "message": "Check the return value.", "severity": "low"}
        raw = {"findings": [
            {**valid, "line": 1, "quote": "old"}, {**valid, "quote": "corrected"},
            {**valid, "path": "other.py"}, {**valid, "line": "2"},
            {**valid, "severity": "critical"}, {**valid, "extra": 3}, valid, valid,
        ]}
        results = validate_ai(raw, [source])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["evidence_sha256"], hashlib.sha256(b"  corrected").hexdigest())

    def test_ai_provider_output_cannot_cite_a_line_outside_the_sent_budget(self):
        lines = {n: f"print({n})" for n in range(1, 252)}
        source = Source("test.py", "", lines)
        proposed = {"findings": [
            {"path": "test.py", "line": n, "quote": lines[n], "message": "Check output.",
             "severity": "low"} for n in (1, 251)
        ]}
        client = MagicMock()
        client.__enter__.return_value = client
        client.post.return_value = httpx.Response(200, request=httpx.Request("POST", "https://example.com"), json={
            "candidates": [{"content": {"parts": [{"text": json.dumps(proposed)}]}}],
            "usageMetadata": {"totalTokenCount": 88},
        })
        with patch.multiple(get_settings(), pr_ai_enabled=True, google_api_key="test-key"), patch(
            "app.platform_review.pipeline.httpx.Client", return_value=client,
        ):
            findings, status, usage = ai_review([source], [])
        self.assertEqual([item["line"] for item in findings], [1])
        self.assertEqual((status, usage), ("completed", {"totalTokenCount": 88}))

    def test_real_semgrep_uses_stable_rule_ids_and_added_lines(self):
        code = "def fresh(xs=[]):\n    return xs\n\ndef unchanged(xs=[]):\n    return xs\n"
        rows, status = scan([Source("demo.py", code, {1: "def fresh(xs=[]):"})])
        self.assertEqual(status, "completed")
        self.assertEqual([(item["rule_id"], item["line"]) for item in rows],
                         [("python-mutable-default", 1)])

    def test_sandbox_disabled_without_subprocess(self):
        with patch.object(get_settings(), "sandbox_enabled", False), patch(
            "app.platform_review.sandbox.bounded_process"
        ) as runner:
            self.assertEqual(verify_python("x = 1", ""), {"status": "disabled"})
            runner.assert_not_called()

    def test_sandbox_argv_and_cleanup(self):
        info = {"MemoryLimit": True, "SwapLimit": True, "CpuCfsQuota": True,
                "PidsLimit": True, "SecurityOptions": ["name=seccomp,profile=builtin"]}
        with patch.object(get_settings(), "sandbox_enabled", True), patch(
            "app.platform_review.sandbox.bounded_process",
            side_effect=[(0, json.dumps(info).encode(), b""), (0, b"", b""), (0, b"", b"")],
        ) as runner:
            self.assertEqual(verify_python("x = 1", "import unittest")["status"], "passed")
        argv = runner.call_args_list[1].args[0]
        for limit in ("--network=none", "--read-only", "--cap-drop=ALL",
                      "--security-opt=no-new-privileges", "--memory=128m",
                      "--cpus=0.5", "--pids-limit=32", "--pull=never"):
            self.assertIn(limit, argv)
        self.assertEqual(runner.call_args_list[1].kwargs["timeout"], 25)
        self.assertEqual(runner.call_args_list[2].args[0][:3], ["docker", "rm", "-f"])

    def test_sandbox_fails_closed_when_resource_limits_are_unsupported(self):
        with patch.object(get_settings(), "sandbox_enabled", True), patch(
            "app.platform_review.sandbox.bounded_process", return_value=(0, b"{}", b"")
        ) as runner:
            self.assertEqual(verify_python("x = 1", "import unittest")["status"], "isolation_unavailable")
            runner.assert_called_once()

    @unittest.skipUnless(os.getenv("CODEGUARD_TEST_DOCKER") == "1", "Docker integration opt-in")
    def test_live_docker_verification(self):
        with patch.object(get_settings(), "sandbox_enabled", True):
            tests = ("import unittest\nfrom submission import add\n"
                     "class TestAdd(unittest.TestCase):\n"
                     "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n")
            self.assertEqual(verify_python("def add(a,b): return a+b", tests)["status"], "passed")
            self.assertEqual(verify_python("def add(a,b): return a-b", tests)["status"], "failed")


class GitHubTests(unittest.TestCase):
    head = "a" * 40
    base = "b" * 40

    def test_source_fetch_checks_sha_context_and_added_lines(self):
        requests = []

        def handler(request):
            requests.append(request)
            path = request.url.path
            if path.endswith("/files"):
                return httpx.Response(200, json=[{
                    "filename": "lib/demo.py", "status": "modified", "additions": 1,
                    "patch": "@@ -1,2 +1,2 @@\n keep\n-old\n+new",
                }])
            if "/contents/" in path:
                return httpx.Response(200, text="keep\nnew\n")
            return httpx.Response(200, json={
                "head": {"sha": self.head}, "base": {"sha": self.base},
                "state": "open", "changed_files": 1,
            })

        github = GitHubApp("octo/demo", 123, 45, 1)
        github.client.close()
        with httpx.Client(base_url="https://api.github.com", transport=httpx.MockTransport(handler)) as client:
            github.client = client
            sources, skipped = github.sources(self.head, self.base)
            self.assertEqual(skipped, 0)
            self.assertEqual(sources[0].added, {2: "new"})
            self.assertEqual(requests[2].url.params["ref"], self.head)
            with self.assertRaises(StaleReview):
                github.sources("f" * 40, self.base)

    def test_installation_credentials_are_scoped_to_one_repository(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import jwt

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        keyfile = Path(self.enterContext(tempfile.TemporaryDirectory())) / "app.pem"
        keyfile.write_bytes(private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
        github = GitHubApp("octo/demo", 123, 45, 1)

        def handler(request):
            self.assertEqual(request.url.path, "/app/installations/45/access_tokens")
            claims = jwt.decode(request.headers["Authorization"].removeprefix("Bearer "),
                                private_key.public_key(), algorithms=["RS256"])
            self.assertEqual(claims["iss"], "891")
            self.assertEqual(json.loads(request.content), {
                "repository_ids": [123], "permissions": {"contents": "read", "pull_requests": "read"},
            })
            return httpx.Response(201, json={"token": "installation-token"})

        github.client.close()
        github.client = httpx.Client(base_url="https://api.github.com", transport=httpx.MockTransport(handler))
        with patch.multiple(github.settings, github_app_id="891",
                            github_app_private_key_file=str(keyfile), github_publish_reviews=False):
            with github:
                self.assertEqual(github.client.headers["Authorization"], "Bearer installation-token")

    def test_publish_only_active_deterministic_comments_and_deduplicates(self):
        calls = []
        body = "CodeGuard automated review.\n<!-- codeguard-review:job-id -->"

        def request(method, path, **kwargs):
            if method == "POST":
                calls.append(kwargs["json"])
                return {"id": 1}
            return [{"body": body, "user": {"type": "Bot"}}] if calls else []

        github = GitHubApp("octo/demo", 123, 45, 1)
        rows = [{"path": "demo.py", "line": 4, "source": "semgrep", "suppressed": False,
                 "message": "Use a specific exception.", "severity": "medium"}]
        rows += [{**rows[0], "source": "ai"}, {**rows[0], "suppressed": True}]
        with github.client, patch.object(github.settings, "github_publish_reviews", True), patch.object(
            github, "request", side_effect=request,
        ), patch.object(github, "current"):
            self.assertEqual(github.publish("job-id", self.head, self.base, rows), "published")
            self.assertEqual(github.publish("job-id", self.head, self.base, rows), "published")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["commit_id"], self.head)
        self.assertEqual(len(calls[0]["comments"]), 1)
        self.assertEqual(calls[0]["comments"][0]["side"], "RIGHT")
        self.assertEqual(calls[0]["comments"][0]["line"], 4)


class AutomationApiTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        from sqlalchemy import create_engine, event
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{Path(directory) / 'test.db'}")

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        self.addCleanup(engine.dispose)
        factory = sessionmaker(bind=engine)
        self.enterContext(patch("app.main.engine", engine))
        self.enterContext(patch("app.db.database.SessionLocal", factory))
        self.enterContext(patch.object(automation, "SessionLocal", factory))
        self.enterContext(patch.object(jobs, "SessionLocal", factory))
        self.db = factory
        self.client = self.enterContext(TestClient(app))
        self.owner, self.auth = self.signup("first@example.com")
        _, self.other = self.signup("other@example.com")

    def signup(self, email):
        result = self.client.post("/auth/signup", json={"email": email, "password": "correct-horse-battery"})
        self.assertEqual(result.status_code, 201, result.text)
        payload = result.json()
        return payload["user"]["id"], {"Authorization": f"Bearer {payload['access_token']}"}

    def enqueue(self, code="def fresh(xs=[]):\n    return xs\n"):
        result = self.client.post("/automation/jobs", headers=self.auth,
                                  json={"language": "python", "code": code})
        self.assertEqual(result.status_code, 202, result.text)
        return result.json()["id"]

    def test_old_endpoints_and_async_review_sarif_feedback(self):
        benchmark = self.client.post("/analysis/static", headers=self.auth,
                                     json={"language": "python", "code": "def f(a=[]): pass"})
        self.assertEqual(benchmark.status_code, 200, benchmark.text)
        self.assertEqual(self.client.get("/history", headers=self.auth).status_code, 200)
        job_id = self.enqueue()
        api = f"/automation/jobs/{job_id}"
        self.assertEqual(self.client.get(api, headers=self.other).status_code, 404)
        jobs.execute(job_id)
        detail = self.client.get(api, headers=self.auth).json()
        self.assertEqual(detail["status"], "completed", detail)
        self.assertEqual(detail["result"]["semgrep"], "completed")
        findings = detail["findings"]
        self.assertEqual({item["source"] for item in findings}, {"static", "semgrep"})
        self.assertEqual(self.client.get("/automation/jobs", headers=self.auth).json()[0]["id"], job_id)
        feedback_url = f"{api}/findings/{findings[0]['id']}/feedback"
        self.assertEqual(self.client.put(feedback_url, headers=self.auth,
                                        json={"verdict": "false_positive"}).status_code, 200)
        sarif = self.client.get(f"{api}/sarif", headers=self.auth).json()
        self.assertEqual(sarif["runs"][0]["results"][0]["suppressions"][0]["kind"], "external")
        next_job_id = self.enqueue()
        jobs.execute(next_job_id)
        next_detail = self.client.get(f"/automation/jobs/{next_job_id}", headers=self.auth).json()
        self.assertTrue(next_detail["findings"][0]["suppressed"])
        with self.db() as db:
            self.assertIsNone(db.get(ReviewJob, job_id).payload)
        self.assertEqual(self.client.delete("/account", headers=self.auth).status_code, 200)
        with self.db() as db:
            self.assertIsNone(db.get(ReviewJob, job_id))

    def test_public_auth_options_only_disclose_enabled_flows(self):
        with patch.multiple(get_settings(), signup_enabled=False, github_oauth_client_id="test",
                            github_oauth_client_secret=""):
            self.assertEqual(self.client.get("/auth/options").json(), {"signup": False, "github": False})
        with patch.multiple(get_settings(), signup_enabled=True, github_oauth_client_id="test",
                            github_oauth_client_secret="test-secret"):
            self.assertEqual(self.client.get("/auth/options").json(), {"signup": True, "github": True})

    def test_quota_cancel_and_lease_conflict(self):
        ids = [self.enqueue() for _ in range(5)]
        result = self.client.post("/automation/jobs", headers=self.auth,
                                  json={"language": "python", "code": "pass"})
        self.assertEqual(result.status_code, 429)
        lease = jobs.claim(ids[0])
        self.assertIsNotNone(lease)
        self.assertIsNone(jobs.claim(ids[0]))
        self.assertEqual(self.client.post(f"/automation/jobs/{ids[0]}/cancel", headers=self.auth).status_code, 200)
        self.assertFalse(jobs.save_findings(ids[0], lease, [], {}, publishing=False))

    def test_transient_failure_and_lease_recovery(self):
        job_id = self.enqueue()
        with patch.object(jobs, "run_review", side_effect=RuntimeError("temporary")) as run:
            with self.assertLogs(jobs.logger, level="ERROR"):
                jobs.execute(job_id)
        run.assert_called_once()
        with self.db.begin() as db:
            job = db.get(ReviewJob, job_id)
            self.assertEqual(job.status, "queued")
            self.assertEqual(job.attempts, 1)
            job.available_at = jobs.now()
        self.assertIn(job_id, jobs.ready_jobs())
        self.assertIsNotNone(jobs.claim(job_id))

    def test_webhook_signature_allowlist_and_revision_idempotency(self):
        settings = get_settings()
        config = {"github_app_id": "123", "github_webhook_secret": "secret-test-value",
                  "github_allowed_installations": "47", "github_review_owner_id": self.owner}
        event = {"action": "opened", "installation": {"id": 47},
                 "repository": {"id": 9000000001, "full_name": "octo/repo"},
                 "pull_request": {"number": 1, "head": {"sha": "a" * 40}, "base": {"sha": "b" * 40}}}
        webhook = "/automation/github/webhook"

        def deliver(id, *, invalid=False):
            body = json.dumps(event).encode()
            signature = hmac.new(config["github_webhook_secret"].encode(), body, hashlib.sha256).hexdigest()
            return self.client.post(webhook, content=body, headers={
                "X-Hub-Signature-256": "sha256=" + ("0" * 64 if invalid else signature),
                "X-GitHub-Event": "pull_request", "X-GitHub-Delivery": id,
            })

        with patch.multiple(settings, **config):
            self.assertEqual(deliver("abc", invalid=True).status_code, 401)
            first = deliver("abc")
            self.assertEqual(first.status_code, 202, first.text)
            self.assertEqual(deliver("abc").json(), {"id": first.json()["id"], "duplicate": True})
            self.assertEqual(deliver("def").json(), {"id": first.json()["id"], "duplicate": True})
            event["pull_request"]["head"]["sha"] = "c" * 40
            self.assertNotEqual(deliver("xyz").json()["id"], first.json()["id"])
            event["installation"]["id"] = 48
            self.assertEqual(deliver("blocked").status_code, 403)
        with self.db() as db:
            self.assertEqual(len(db.scalars(select(ReviewJob)).all()), 2)
        self.assertEqual(self.client.get("/automation/jobs", headers=self.other).json(), [])
