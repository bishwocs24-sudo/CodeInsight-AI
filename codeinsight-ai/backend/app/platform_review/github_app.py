import html
import json
import re
import time
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import httpx
import jwt

from app.core.config import get_settings
from app.platform_review.evidence import LANGUAGES, Source, added_lines

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,99}/[A-Za-z0-9_.-]{1,100}")
SHA = re.compile(r"[a-f0-9]{40}")
MAX_FILES = 60


class RemoteFailure(RuntimeError):
    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.retryable = retryable


class StaleReview(Exception):
    pass


class GitHubApp:
    def __init__(self, repository: str, repository_id: int, installation_id: int, number: int):
        self.settings = get_settings()
        self.client = httpx.Client(
            base_url="https://api.github.com", timeout=8, follow_redirects=False,
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        )
        self.repository_id = repository_id
        self.installation_id = installation_id
        self.repository = f"/repos/{repository}"
        self.pull = f"{self.repository}/pulls/{number}"

    def __enter__(self):
        try:
            issued = int(time.time())
            key = Path(self.settings.github_app_private_key_file).read_bytes()
            token = jwt.encode(
                {"iat": issued - 30, "exp": issued + 540, "iss": self.settings.github_app_id},
                key, algorithm="RS256",
            )
            self.client.headers["Authorization"] = f"Bearer {token}"
            result = self.request(
                "POST", f"/app/installations/{self.installation_id}/access_tokens",
                json={"repository_ids": [self.repository_id], "permissions": {
                    "contents": "read", "pull_requests": (
                        "write" if self.settings.github_publish_reviews else "read"
                    ),
                }},
            )
            self.client.headers["Authorization"] = f"Bearer {result['token']}"
            return self
        except (OSError, ValueError, jwt.PyJWTError) as exc:
            self.client.close()
            raise RemoteFailure("GitHub App credentials are invalid") from exc
        except Exception:
            self.client.close()
            raise

    def __exit__(self, *_):
        self.client.close()

    def request(self, method, path, *, raw=False, limit=2_000_000, **kwargs):
        try:
            with self.client.stream(method, path, **kwargs) as response:
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > limit:
                        raise RemoteFailure("GitHub response exceeds the review size limit")
                return bytes(content) if raw else json.loads(content)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            retryable = status in {408, 429} or status >= 500 or (
                status == 403 and ("retry-after" in exc.response.headers or
                                   exc.response.headers.get("x-ratelimit-remaining") == "0")
            )
            if raw and status in {404, 422}:
                return b""
            raise RemoteFailure(f"GitHub returned HTTP {status}", retryable) from exc
        except httpx.RequestError as exc:
            raise RemoteFailure("GitHub connection failed", retryable=True) from exc

    def current(self, head, base):
        pr = self.request("GET", self.pull)
        if pr["head"]["sha"] != head or pr["base"]["sha"] != base or pr["state"] != "open":
            raise StaleReview("The pull request changed before review completed")
        return pr

    def sources(self, head, base):
        pr = self.current(head, base)
        files = self.request("GET", f"{self.pull}/files", params={"per_page": MAX_FILES})
        sources = []
        skipped = max(pr["changed_files"] - len(files), 0)
        remaining = 300_000
        deadline = time.monotonic() + 100
        for index, item in enumerate(files):
            if time.monotonic() >= deadline:
                skipped += len(files) - index
                break
            if item["status"] == "removed":
                continue
            path = item["filename"]
            if PurePosixPath(path).suffix not in LANGUAGES:
                skipped += 1
                continue
            lines = added_lines(item.get("patch") or "")
            if not lines or len(lines) != item["additions"] or remaining < 1 or len(path) > 500:
                skipped += 1
                continue
            try:
                raw = self.request(
                    "GET", f"{self.repository}/contents/{quote(path, safe='/')}", raw=True,
                    limit=min(80_000, remaining), params={"ref": head},
                    headers={"Accept": "application/vnd.github.raw+json"},
                )
                text = raw.decode("utf-8")
            except (UnicodeError, RemoteFailure) as exc:
                if isinstance(exc, RemoteFailure) and exc.retryable:
                    raise
                skipped += 1
                continue
            actual = text.split("\n")
            if "\0" in text or any(
                index > len(actual) or actual[index - 1].removesuffix("\r") != value
                for index, value in lines.items()
            ):
                skipped += 1
                continue
            remaining -= len(raw)
            sources.append(Source(path, text, lines))
        self.current(head, base)
        return sources, skipped

    def publish(self, job_id, head, base, findings):
        if not self.settings.github_publish_reviews:
            return "disabled"
        comments = []
        seen = set()
        for item in findings:
            if item["suppressed"] or item["source"] == "ai":
                continue
            location = (item["path"], item["line"])
            if location in seen:
                continue
            seen.add(location)
            message = html.escape(item["message"]).replace("@", "&#64;")
            comments.append({
                "path": item["path"], "line": item["line"], "side": "RIGHT",
                "body": f"**CodeGuard AI · {item['severity'].title()}**\n\n{message}",
            })
        if not comments:
            return "no_comments"
        self.current(head, base)
        marker = f"<!-- codeguard-review:{job_id} -->"
        for page in range(1, 11):
            reviews = self.request("GET", f"{self.pull}/reviews", params={"per_page": 100, "page": page})
            if any(marker in (review.get("body") or "") and
                   (review.get("user") or {}).get("type") == "Bot" for review in reviews):
                return "published"
            if len(reviews) < 100:
                break
        else:
            raise RemoteFailure("Too many existing GitHub reviews to safely publish")
        self.current(head, base)
        self.request("POST", f"{self.pull}/reviews", json={
            "commit_id": head, "event": "COMMENT", "body": f"CodeGuard automated review.\n{marker}",
            "comments": comments[:15],
        })
        return "published"
