# CodeGuard AI — architecture assessment and upgrade roadmap

The milestone list below describes the original implementation plan. See [Review automation](REVIEW_AUTOMATION.md) for the current implementation, supported workflows, setup, and verification.


## Existing system (verified in uploaded source)
Next.js frontend, FastAPI API, Gemini JSON-based analyses, JWT authentication, PostgreSQL/SQLAlchemy review history, GitHub public-repository file import, source-file upload and PDF reporting.

## Implemented in this upgrade
- Independent, non-executing static-analysis engine for Python, JS/TS and C/C++.
- Structured findings with rule IDs, source locations, evidence, severity and confidence classification.
- Authenticated `POST /analysis/static` endpoint using existing `ReviewRequest` schema.
- Six deterministic regression tests; no LLM key required.

Example request (authenticated):
`POST /analysis/static` with JSON `{ "language": "python", "code": "eval(user_input)" }`.

Run tests: `cd backend && PYTHONPATH=. python -m unittest discover -s tests -v`

## Critical next engineering milestones
1. **Pull request integration**: GitHub App installation, least-privilege credentials, webhook signature verification, idempotency, fetch changed lines, review only the diff and publish line comments. Never blindly execute external PR code.
2. **SAST integration**: Semgrep subprocess in a resource-limited worker (no shell interpolation); SARIF-compatible findings, suppression controls and rule-version tracking.
3. **Review orchestration**: Redis + Celery/RQ worker, job lifecycle and cancellation, request quotas, retry policy, provider timeouts, cached review results by commit SHA.
4. **AI evidence pipeline**: send deterministic findings and diff context to the LLM; require validated structured output and cite exact changed lines. Treat repository text as untrusted instructions.
5. **Patch verification**: run tests in an isolated container with networking disabled, CPU/memory/time limits and disposable filesystem; do not run arbitrary code in the API process.
6. **Persistence**: Alembic migrations; normalized repository, pull request, finding, job and feedback tables; store minimal source data and add retention controls.
7. **Security**: rotate JWT secrets, add rate limits, restrict GitHub OAuth scopes, secure tokens at rest, improve CORS, audit dependency vulnerabilities.
8. **Evaluation**: curated labeled bug benchmark, precision/recall, false-positive rates, review latency, per-review cost, regression test suite and CI gates.

## Known limitations
- New static checks are heuristic, not a full security audit; JS/C patterns can match comments or strings.
- This release does not yet automate pull-request review, execute tests, or add new frontend pages.
- Live end-to-end testing requires configured database and authentication; only isolated analyzer unit tests were executed here.
- Review existing auth, GitHub and upload paths before production deployment.

## Suggested portfolio narrative
"Developed a hybrid code-analysis architecture combining deterministic static checks with LLM-assisted reviews; introduced evidence-linked security findings, an authenticated scanning API and automated regression tests." Add actual benchmark results only after measuring them.
