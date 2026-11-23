# Review automation

Open **Dashboard → Review queue** to submit a snippet, inspect the source and severity of each finding, suppress false positives, and export SARIF. The same queue shows pull request reviews for the configured GitHub App operator. Existing interactive analyses, GitHub imports, history, analytics, account settings, and PDF export use their original routes.

## Start locally

Use Linux with Python 3.12, Node.js 22 or newer, and `prlimit` from util-linux. From the repository root, start PostgreSQL and Redis with `docker compose up -d db redis`. Then run:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m venv .scanner
.scanner/bin/pip install -r requirements-scanner.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --port 8000
```

From two terminals in `backend`, use the same API virtual environment and configuration. Set `SEMGREP_BINARY` in `.env` to the absolute path of `backend/.scanner/bin/semgrep` before starting the worker. Keep the scanner virtual environment separate from the API environment.

```bash
celery -A app.platform_review.worker:celery worker --loglevel=INFO --concurrency=2
```

```bash
celery -A app.platform_review.worker:celery beat --loglevel=INFO
```

From another terminal, run:

```bash
cd frontend
npm ci
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000), create an account, and use **New scan** in the review queue. Semgrep and the built-in analyzer run without Gemini. For a Docker-free development setup, use `DATABASE_URL=sqlite:///codeguard.db`, run the same migration, and substitute `python -m app.platform_review.worker local` for Celery and beat.

### Existing databases

For an original installation that used SQLAlchemy table creation, back up the database and confirm `users`, `reviews`, and `settings` match the schema in `0001_legacy.py`. Then run `alembic stamp 0001_legacy` and `alembic upgrade head`. An empty database needs only `alembic upgrade head`. Run migrations before starting production processes. Avoid starting the development API against an unmigrated database if you intend to track the schema with Alembic.

## Configure a GitHub App

1. Create an operator account and fetch its internal UUID from the authenticated `GET /auth/me` response. Set `GITHUB_REVIEW_OWNER_ID` to that UUID.
2. Set the GitHub App webhook URL to your public HTTPS origin followed by `/automation/github/webhook`. Set a random webhook secret on both the App and `GITHUB_WEBHOOK_SECRET`.
3. Subscribe to **Pull request** events. Give the App **Contents** read and **Pull requests** read for scan-only use, or **Pull requests** write to publish inline findings. Install it only on the selected repositories.
4. Set `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_FILE`, and comma-separated `GITHUB_ALLOWED_INSTALLATIONS`. Mount the private key read-only for the worker. The API needs the webhook secret. Installation tokens are scoped to one repository and remain in worker memory.
5. Open a test PR and inspect the recorded head commit and coverage. Set `GITHUB_PUBLISH_REVIEWS=true` to enable inline comments. Previously processed commits stay cached under their original policy. GitHub App credentials and GitHub OAuth sign-in credentials are separate.

The webhook verifies HMAC-SHA256 over the exact request bytes. Open, reopen, synchronize, and ready-for-review events enqueue work for non-draft PRs. A delivery ID and a unique PR/base/head/policy combination deduplicate jobs. The worker verifies the current PR revision and compares each added line with the commit-pinned file before reviewing it. Truncated, inaccessible, binary, and unsupported files can be skipped. The scan tracks that coverage. Bounds include 60 changed files, 80 KB per file, 300 KB of source per job, and 150 findings. GitHub publication is limited to 15 deterministic inline locations and uses a review marker to reconcile a retry after an ambiguous response. AI suggestions remain visible in the dashboard.

## Enable grounded AI

Set `GOOGLE_API_KEY` and opt in with `PR_AI_ENABLED=true`. This sends bounded added lines and deterministic finding metadata to Gemini for asynchronous PR and snippet reviews. Only enable it for repositories whose owners allow that transfer. A model result is accepted only when its path, line number, and exact quote match submitted review evidence. The review stores an evidence hash and location. Provider errors leave deterministic findings available. Token counts and latency are recorded when available.

## Enable isolated test verification

Build a trusted runner image on a dedicated Docker worker host.

```bash
docker build -f backend/Dockerfile.runner -t codeguard-python-runner:local backend
```

Set `SANDBOX_ENABLED=true` on the API and worker. Optionally use `SANDBOX_DOCKER_HOST` to select a dedicated local Unix socket accessible to that worker. The worker and daemon must see the same temporary directory path. The runner checks that the daemon enforces CPU, memory, swap, process, and seccomp limits. The runtime uses an offline disposable container with a read-only root, no capabilities, a non-root user, bounded temporary storage and output, and a 25-second execution budget. It uses a prebuilt image and never installs dependencies from the submission.

For an explicit Python snippet test, import the submitted code from `submission` in a `unittest.TestCase`. The standard Python library is available. Webhook jobs never execute PR source code. For hostile internet-facing workloads, keep execution disabled until the worker and runner daemon are placed on a dedicated, disposable host or equivalent hardened isolation boundary. The runner does not support arbitrary test commands, other languages, or checkout-based PR test verification.

## Operation and verification

- PostgreSQL is the source of truth. Celery beat dispatches due records over Redis. Leases protect work against duplicate queue deliveries. Transient failures retry with backoff up to three attempts. Cancellation blocks saving or publishing while a job is queued or running. A scanner or container already in flight may finish within its timeout.
- A false-positive verdict suppresses that fingerprint on future reviews of the same repository or subsequent snippets for the same account. Findings and feedback expire with their jobs after `REVIEW_RETENTION_DAYS`. Temporary source files are discarded, and queued snippet payloads are cleared on terminal transitions. The legacy history still retains code according to its existing settings. Use encryption at rest on production database volumes and backups.
- Use a unique JWT secret, restricted signup, HTTPS, a dedicated frontend origin, and a private authenticated Redis instance. The production API enforces Redis-backed per-IP authentication limits. Configure trusted proxy addresses so it sees client IPs, and apply request body limits at the ingress. Account deletion cascades to automation jobs and findings. Automatic OAuth linking by email was removed for password accounts. Existing linked GitHub identities can still sign in.
- Run `python -m unittest discover -s tests -v` from `backend` with Semgrep and util-linux on `PATH`. Set `CODEGUARD_TEST_DOCKER=1` to run live container smoke tests after building the runner image.
- Run `PYTHONPATH=. python evaluation/run.py --gate` from `backend` for the labeled benchmark. It measures unique added-line precision, recall, false-positive rate, and median latency. With AI enabled, optionally pass per-million-token prices to report an estimate. The eight curated fixtures are regression coverage and do not estimate field performance.

The API requirements and frontend production dependencies passed dependency audits at release verification. The standalone Semgrep 1.186.0 environment has upstream advisories in transitive MCP, OpenTelemetry, and glob-matching packages. CodeGuard invokes Semgrep's local scan command with a bundled ruleset and a scrubbed environment. Keep that installation on the constrained worker, restrict worker egress to the required review APIs, and refresh the scanner pin as patched upstream packages become available.

### Verification of this release

The production frontend build, lint, TypeScript check, and Alembic schema check passed. Chromium completed signup, queued a snippet, received real Semgrep and static findings through Redis/Celery and PostgreSQL, submitted feedback, downloaded SARIF, and checked the review queue at mobile width. The backend suite passed 20 tests. Its opt-in Docker smoke test requires a compatible daemon. Signed GitHub events, installation authentication, inline comment publication, and Gemini evidence validation were exercised with test fixtures. Live GitHub and Gemini credentials were unavailable for this verification.

The curated eight-case benchmark detected all four labeled issue locations, produced no false positives on its seven labeled clean locations, and recorded about 3.0 seconds median latency with AI disabled.
