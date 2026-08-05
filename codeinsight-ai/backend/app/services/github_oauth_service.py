"""
GitHub OAuth ("Login with GitHub") - the authorization code exchange
and profile fetch. Separate from GitHubService (which browses public
repos) because this one needs client credentials and handles a
different kind of token.
"""
import httpx

from app.core.config import get_settings


class GitHubOAuthError(Exception):
    pass


class GitHubOAuthService:
    def __init__(self):
        self._settings = get_settings()
        self._client = httpx.Client(timeout=15)

    def authorize_url(self) -> str:
        params = (
            f"client_id={self._settings.github_oauth_client_id}"
            f"&redirect_uri={self._settings.github_oauth_redirect_uri}"
            f"&scope=read:user user:email"
        )
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

        email = user.get("email")
        if not email:
            # Primary email is often private - fall back to the emails endpoint.
            emails_resp = self._client.get("https://api.github.com/user/emails", headers=headers)
            emails_resp.raise_for_status()
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            email = primary["email"] if primary else (emails[0]["email"] if emails else None)

        if not email:
            raise GitHubOAuthError("Couldn't get an email address from your GitHub account.")

        return {"id": str(user["id"]), "email": email, "login": user.get("login")}
