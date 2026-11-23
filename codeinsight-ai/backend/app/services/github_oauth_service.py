"""
GitHub OAuth ("Login with GitHub") - the authorization code exchange
and profile fetch. Separate from GitHubService (which browses public
repos) because this one needs client credentials and handles a
different kind of token.
"""
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


class GitHubOAuthError(Exception):
    pass


class GitHubOAuthService:
    def __init__(self):
        self._settings = get_settings()
        self._client = httpx.Client(timeout=15)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._client.close()

    def authorize_url(self, state: str) -> str:
        params = urlencode({
            "client_id": self._settings.github_oauth_client_id,
            "redirect_uri": self._settings.github_oauth_redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        })
        return f"https://github.com/login/oauth/authorize?{params}"

    def exchange_code_for_token(self, code: str) -> str:
        resp = self._client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": self._settings.github_oauth_client_id,
                "client_secret": self._settings.github_oauth_client_secret,
                "code": code,
                "redirect_uri": self._settings.github_oauth_redirect_uri,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise GitHubOAuthError(data.get("error_description", "GitHub didn't return an access token."))
        return token

    def get_profile(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}

        user_resp = self._client.get("https://api.github.com/user", headers=headers)
        user_resp.raise_for_status()
        user = user_resp.json()

        emails_resp = self._client.get("https://api.github.com/user/emails", headers=headers)
        emails_resp.raise_for_status()
        emails = [entry for entry in emails_resp.json() if entry.get("verified")]
        primary = next((entry for entry in emails if entry.get("primary")), None)
        email = (primary or (emails[0] if emails else {})).get("email")
        if not email:
            raise GitHubOAuthError("GitHub sign-in requires a verified email address.")

        return {"id": str(user["id"]), "email": email, "login": user.get("login")}
