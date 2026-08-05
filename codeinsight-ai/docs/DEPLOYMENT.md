# Deployment

This covers deploying to the stack named in the original spec: Vercel
(frontend), Render (backend), Neon (Postgres). Each step needs an account
on that platform — nothing here can be done without you creating them.

## 1. Database — Neon
1. Create a project at https://neon.tech
2. Copy the connection string it gives you (starts with `postgresql://`)
3. That's your production `DATABASE_URL`

## 2. Backend — Render
1. Push this repo to GitHub.
2. In Render, **New → Web Service**, connect the repo, set root directory to `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `DATABASE_URL` → your Neon connection string
   - `GOOGLE_API_KEY` → your Gemini key
   - `GOOGLE_MODEL` → `gemini-2.5-flash`
   - `FRONTEND_ORIGIN` → your Vercel URL once you have it (step 3)
6. Before going live, replace `Base.metadata.create_all()` in
   `app/main.py` with real Alembic migrations — `create_all` is fine for
   local dev but doesn't handle schema changes safely in production.

A `render.yaml` is included in this repo so you can also use Render's
"New → Blueprint" flow instead of manual setup.

## 3. Frontend — Vercel
1. In Vercel, **New Project**, import the same repo, set root directory to `frontend`.
2. Add environment variable:
   - `NEXT_PUBLIC_API_URL` → your Render backend URL from step 2
3. Deploy. Vercel auto-detects Next.js — no build config needed.

## 4. Wire CORS
Once both are deployed, go back to Render and make sure
`FRONTEND_ORIGIN` exactly matches your Vercel URL (including `https://`),
then redeploy the backend — CORS will reject requests otherwise.

## 5. Auth and file storage
If you've added Clerk (see `AUTH_SETUP.md`), add its production keys as
env vars on both Vercel and Render. Cloudinary (for avatar/file storage,
if you add it later) works the same way — create an account, add the
API key as an env var, never commit it.
