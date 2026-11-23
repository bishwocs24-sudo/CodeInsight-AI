# CodeGuard AI

The asynchronous review queue adds GitHub App pull request reviews, Semgrep, evidence-validated AI suggestions, feedback, SARIF export, and optional isolated Python tests. See [Review automation](docs/REVIEW_AUTOMATION.md) for startup, configuration, migrations, and verification. See [self-hosting at no hosting cost](docs/FREE_DEPLOYMENT.md) for the full stack on a single Linux VM.

Select **Try sample review** from the homepage to explore a recorded Semgrep scan, triage a finding, and download SARIF without an account. The replay uses a fixed snippet and runs entirely in the browser.

AI-powered code review platform. Paste code, upload a file, or connect a
public GitHub repo; run an AI review/security/refactor/test/explain/complexity
pass; see structured results with charts, diffs, and PDF export — backed by
a real Postgres database and the Google AI Studio (Gemini) API.

**Fully working today:** email/password authentication (signup, login, per-user
data isolation), code review (all 6 analysis types), file upload, GitHub public
repo import + per-file review + repo health score, review history, analytics
with charts, PDF/JSON export, a real settings page, diff viewer, copy buttons,
autosave, and a keyboard shortcut (`Ctrl+Enter`).

Password authentication is built in. GitHub App automation, GitHub sign-in, and Gemini reviews require their respective credentials. The [Render Blueprint](render.yaml) closes public registration by default.

## Architecture

```
codeinsight-ai/
├── docker-compose.yml      # Postgres for local dev
├── render.yaml             # Render blueprint for backend deployment
├── docs/
│   ├── AUTH_SETUP.md       # how to wire in Clerk with your own account
│   └── DEPLOYMENT.md       # Vercel + Render + Neon deployment steps
├── backend/                # FastAPI
│   └── app/
│       ├── core/           # settings
│       ├── db/             # SQLAlchemy engine/session
│       ├── models/         # ORM models (Review, Settings)
│       ├── schemas/        # Pydantic request/response models
│       ├── prompts/        # modular prompt templates (never inline in routes)
│       ├── services/       # AIService, GitHubService, pdf_service — external calls live here only
│       ├── repositories/   # ReviewRepository — the only place that queries the DB
│       └── api/routes/     # review.py, history.py, github.py, upload.py, settings.py
└── frontend/                # Next.js App Router + TypeScript + Tailwind
    ├── app/
    │   ├── page.tsx                    # landing page
    │   └── dashboard/
    │       ├── layout.tsx              # sidebar + navbar
    │       ├── page.tsx                # overview
    │       ├── new-review/page.tsx     # Monaco editor + actions + results + diff/upload/autosave
    │       ├── history/page.tsx        # past reviews + PDF export
    │       ├── github/page.tsx         # connect repo, per-file review, health score
    │       ├── analytics/page.tsx      # recharts usage charts
    │       ├── settings/page.tsx       # preferences + delete account
    │       └── profile/page.tsx        # placeholder until auth is added
    ├── components/         # Button, Card, Badge, CodeEditor, ScoreCard, CopyButton, DiffViewer
    └── lib/                # api.ts (typed fetch client), types.ts
```

Design pattern: routes → repositories/services → models. Prompts are
templated functions, never string-concatenated in the route layer, so you
can edit prompt wording in one file without touching request handling.

## Prerequisites

- Node.js 22+
- Python 3.11+
- Docker (for Postgres) — or point `DATABASE_URL` at any Postgres instance
- A Google AI Studio (Gemini) API key — free, no credit card: https://aistudio.google.com/apikey

## Setup

### 1. Database

```bash
docker compose up -d
```

This starts Postgres on `localhost:5432` with user/pass/db all `codeinsight`.

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GOOGLE_API_KEY
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on startup (`Base.metadata.create_all`).
Swap this for Alembic migrations before deploying to production.

Visit http://localhost:8000/health — should return `{"status": "ok"}`.
Interactive API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Visit http://localhost:3000

## Environment variables

**backend/.env**
| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `GOOGLE_API_KEY` | Your Google AI Studio (Gemini) API key |
| `GOOGLE_MODEL` | Model id, defaults to `gemini-2.5-flash` |
| `FRONTEND_ORIGIN` | Allowed CORS origin |
| `JWT_SECRET_KEY` | Signing secret for login tokens — change before deploying anywhere real |
| `GITHUB_OAUTH_CLIENT_ID` / `GITHUB_OAUTH_CLIENT_SECRET` | Optional — enables "Login with GitHub". See `docs/AUTH_SETUP.md` |
| `GITHUB_OAUTH_REDIRECT_URI` | Where GitHub redirects after auth, defaults to `http://localhost:8000/auth/github/callback` |
| `FRONTEND_AUTH_CALLBACK_URL` | Where the backend sends the user after GitHub auth, defaults to `http://localhost:3000/auth/callback` |

**frontend/.env.local**
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL, defaults to `http://localhost:8000` |

## API routes (implemented)

| Route | Description |
|---|---|
| `POST /auth/signup` / `POST /auth/login` | Email/password auth, returns a JWT |
| `GET /auth/me` | Current signed-in user |
| `GET /auth/github/login` / `GET /auth/github/callback` | GitHub OAuth flow |
| `POST /review` | Full code review — scores, strengths, weaknesses, bugs, smells |
| `POST /security` | Security scan — vulnerabilities with CWE + remediation |
| `POST /refactor` | Refactored code, behavior-preserving |
| `POST /tests` | Generated unit tests in the idiomatic framework |
| `POST /explain` | Beginner-friendly explanation |
| `POST /complexity` | Time/space Big-O with bottlenecks |
| `GET /history` | Recent reviews (id, language, type, score, date) |
| `GET /history/{id}` | Full stored result for one review |
| `GET /history/{id}/pdf` | Downloadable PDF report for one review |
| `GET /analytics` | Reviews completed, average score, language breakdown |
| `POST /upload` | Reads an uploaded source file, returns its code + detected language |
| `POST /github/import` | Lists reviewable files in a public GitHub repo |
| `POST /github/review-file` | Runs a full review on one file from a connected repo |
| `POST /github/health-score` | Reviews up to 8 files and returns an aggregate repo health score |
| `GET /settings` / `PATCH /settings` | Read/update app preferences |
| `DELETE /account` | Deletes the signed-in user's reviews, settings, and account |

Every route above except the `/auth/*` ones requires an `Authorization: Bearer <token>`
header — the frontend handles this automatically once you're logged in.

## First run
Visit http://localhost:3000 — you'll land on the landing page. Click
**Start Reviewing** (or **Sign in**) to reach `/signup`, create an account
with email/password (or GitHub, if configured — see `docs/AUTH_SETUP.md`),
and you'll be dropped into the dashboard.

## Still needs your own setup

These need accounts/credentials only you can create — see the linked docs:

1. **GitHub OAuth login** (`docs/AUTH_SETUP.md`) — email/password auth already works with zero setup; "Login with GitHub" needs a free GitHub OAuth App (2-minute setup, your own client id/secret)
2. **Deployment** (`docs/DEPLOYMENT.md`) — Vercel (frontend), Render (backend, `render.yaml` included), Neon (DB)
3. **Billing** — the pricing page's Pro/Team buttons are intentionally disabled with an explanation; there's no usage limit enforced yet, so Free currently covers everything. Wiring real payment needs your own Stripe account.
4. **Cloudinary** — only needed if you add avatar/asset storage later; not required for anything currently in the app

Everything else in the original spec is built and working. Tell me if you
want anything adjusted and I'll do it the same way — real code, no stubs.
