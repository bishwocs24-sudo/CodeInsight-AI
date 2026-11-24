# GitHub sign-in for the Vercel demo

The public sample review remains available without signing in. The hosted login uses GitHub OAuth and an encrypted session cookie, without a separate database. This session shows the signed-in GitHub identity on the demo; live scans and the full dashboard still use the separate CodeGuard backend.

## Register the OAuth app

In [GitHub OAuth app settings](https://github.com/settings/developers), register a new **OAuth App** for CodeGuard AI.

- Homepage URL: `https://codeguard-ai-demo.vercel.app`
- Authorization callback URL: `https://codeguard-ai-demo.vercel.app/api/auth/callback/github`

Generate a client secret. In Vercel, open the `codeguard-ai-demo` project's Environment Variables settings and set these variables for **Production**:

| Key | Value |
| --- | --- |
| `AUTH_GITHUB_ID` | OAuth app client ID |
| `AUTH_GITHUB_SECRET` | OAuth app client secret |
| `AUTH_SECRET` | A separate randomly generated secret of at least 32 characters, for example from `openssl rand -base64 32` |
| `AUTH_URL` | `https://codeguard-ai-demo.vercel.app` |

Store the secret values directly in Vercel. Redeploy the updated commit to Production, open `/login/`, choose **Continue with GitHub**, and confirm the account page and sign-out work. The demo leaves sign-in disabled when any required credentials are missing and restricts the OAuth flow to the configured origin.

## Public snippet scanning

The Vercel build includes a live scanner at `/scan/`. It accepts pasted snippets and UTF-8 files up to 24 KB and returns line evidence from built-in rules. No account, provider key, database, or worker is required for this scanner. Submitted code is analyzed without execution, and results can be downloaded as SARIF.

The Vercel function packages a copy of the dependency-free backend analyzer because the Vercel project root is the frontend directory. If you change `backend/app/services/static_analysis.py`, copy it to `frontend/lib/hosted_python/static_analysis.py` before deploying. The hosted scan tests check that the copies match.

See [Free deployment](FREE_DEPLOYMENT.md) to run the full background worker, Semgrep, PR automation, and persistent review history.
