"""
GitHub service.

Works against PUBLIC repositories only, using unauthenticated GitHub
REST API calls (60 requests/hour rate limit). To support private
repos, this would need GitHub OAuth (via Clerk or a standalone OAuth
app) so calls carry a user access token - that's a follow-up slice
that needs your own GitHub OAuth App credentials.
"""
import base64
import re

import httpx

GITHUB_API = "https://api.github.com"

# Extensions we'll actually offer for review - skips binaries, images, locks, etc.
REVIEWABLE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".kt", ".swift", ".rb", ".php", ".java",
}

EXT_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".go": "go", ".rs": "rust",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".cs": "csharp",
    ".kt": "kotlin", ".swift": "swift", ".rb": "ruby", ".php": "php",
    ".java": "java",
}


class GitHubServiceError(Exception):
    pass


def parse_repo_url(url: str) -> tuple[str, str]:
    """Extracts (owner, repo) from a GitHub URL or 'owner/repo' shorthand."""
    url = url.strip().rstrip("/")
    match = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?$", url)
    if match:
        return match.group(1), match.group(2)
    if re.match(r"^[\w.-]+/[\w.-]+$", url):
        owner, repo = url.split("/", 1)
        return owner, repo
    raise GitHubServiceError(
        "Couldn't parse that as a GitHub repo. Use a URL like "
        "https://github.com/owner/repo or just 'owner/repo'."
    )


class GitHubService:
    def __init__(self):
        self._client = httpx.Client(
            base_url=GITHUB_API,
            headers={"Accept": "application/vnd.github+json"},
            timeout=15,
        )

    def get_repo_info(self, owner: str, repo: str) -> dict:
        resp = self._client.get(f"/repos/{owner}/{repo}")
        if resp.status_code == 404:
            raise GitHubServiceError(f"Repository {owner}/{repo} not found (or it's private).")
        if resp.status_code == 403:
            raise GitHubServiceError("GitHub API rate limit hit. Try again in a bit.")
        resp.raise_for_status()
        return resp.json()

    def list_reviewable_files(self, owner: str, repo: str, default_branch: str, limit: int = 25) -> list[dict]:
        resp = self._client.get(f"/repos/{owner}/{repo}/git/trees/{default_branch}", params={"recursive": "1"})
        if resp.status_code == 404:
            raise GitHubServiceError("Couldn't read the repo's file tree.")
        resp.raise_for_status()
        tree = resp.json().get("tree", [])

        files = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item["path"]
            ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
            if ext in REVIEWABLE_EXTENSIONS:
                files.append({
                    "path": path,
                    "sha": item["sha"],
                    "size": item.get("size", 0),
                    "language": EXT_TO_LANGUAGE[ext],
                })
            if len(files) >= limit:
                break
        return files

    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        resp = self._client.get(f"/repos/{owner}/{repo}/contents/{path}")
        resp.raise_for_status()
        data = resp.json()
        if data.get("encoding") != "base64":
            raise GitHubServiceError(f"Unexpected encoding for {path}")
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
