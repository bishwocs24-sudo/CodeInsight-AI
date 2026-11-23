# Deploy CodeGuard on Render

The Blueprint creates a public web service in Singapore, a Celery worker and scheduler, private PostgreSQL, and private Redis-compatible Key Value. The web service serves both the exported Next.js frontend and FastAPI at the same HTTPS origin. It applies Alembic migrations before starting and checks PostgreSQL and Key Value readiness. The worker installs Semgrep in a separate virtual environment.

## First deployment

1. Push the contents of this directory to the root of a GitHub repository accessible to your Render workspace. Keep the repository private if you want to restrict source access.
2. In Render, create a Blueprint from that repository and select `render.yaml`. Review the price for the listed paid resources in your workspace before applying the plan.
3. Once the web service deploys, open its HTTPS URL and check `/ready`. The readiness response should be `{"status":"ready"}`.
4. Open the web service's authenticated Render Shell and provision your operator account:

   ```bash
   python -m app.core.create_operator your-email@example.com
   ```

   Enter the password at the prompt. Save the printed operator ID if configuring a GitHub App.
5. Sign in at the web URL, choose **Review queue → New scan**, and submit a short snippet. Confirm the job completes and SARIF downloads.

A public visitor can open **Try sample review** without signing in. It uses results captured from a fixed sample in the real Semgrep and static analysis pipeline. It never submits user code, starts a worker job or calls Gemini.

Public account registration is closed by default. The Blueprint generates the API's signing secret. Keep private GitHub code and unaudited snippets away from any publicly shared demo account.

## Verify the deployed stack

From a checkout with the backend dependencies installed, run:

```bash
cd backend
python evaluation/check_deployment.py https://your-service.onrender.com your-email@example.com
```

The check prompts for the operator password and submits one fixed sample through the normal API. It verifies readiness, the public demo page, the completed worker job, real Semgrep findings, and SARIF export.

## Enable external integrations

Semgrep and the static analyzer are enabled by default. Set a Gemini key via the Render environment group if you want interactive AI reviews. Set `PR_AI_ENABLED=true` there to additionally enable AI in background reviews. Repository owners must approve sending bounded source excerpts to Gemini.

Use the HTTPS web URL plus `/automation/github/webhook` for a GitHub App webhook. Set the App ID, webhook secret, allowlisted installation IDs, operator ID, and optional publication flag in the environment group. Upload the App private key to the worker as a Render secret file and set `GITHUB_APP_PRIVATE_KEY_FILE` to its runtime path on the worker. See [review automation](REVIEW_AUTOMATION.md) for GitHub permissions and verification. Set GitHub OAuth credentials on the web service separately if you use GitHub sign-in. For a custom domain, explicitly configure the frontend origin and both OAuth callback URLs.

Sandbox test execution is disabled in this Blueprint. Running user-supplied Python tests requires a compatible Docker daemon on an isolated worker host.
