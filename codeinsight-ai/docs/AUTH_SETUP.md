# Authentication

The app has **working authentication already built in** - email/password
signup+login (JWT-based, no external service needed) and GitHub OAuth
("Login with GitHub"). Every review, history entry, and setting is scoped
to the signed-in user.

## Email/password - works out of the box
No setup needed. `POST /auth/signup` and `POST /auth/login` just work
against your own Postgres database as soon as the backend is running.

## GitHub OAuth ("Continue with GitHub") - needs your own free OAuth App
This is a real, working OAuth flow - it just needs credentials only you
can create (GitHub requires every app to register its own client
id/secret; there's no shared one to give you).

### 1. Create a GitHub OAuth App
1. Go to https://github.com/settings/developers -> OAuth Apps -> New OAuth App
2. Fill in:
   - Application name: anything, e.g. `CodeInsight AI (local)`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/auth/github/callback`
3. Click Register application
4. Copy the Client ID, then click Generate a new client secret and copy that too

This takes about 2 minutes and is entirely free - no approval process,
no waiting.

### 2. Add the credentials to backend/.env
```
GITHUB_OAUTH_CLIENT_ID=your-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-client-secret
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/auth/github/callback
FRONTEND_AUTH_CALLBACK_URL=http://localhost:3000/auth/callback
```

### 3. Restart the backend
```
uvicorn app.main:app --reload --port 8000
```

That's it - "Continue with GitHub" on the login/signup pages and the
landing page's "GitHub Login" button will now work. Without these env
vars set, clicking those buttons returns a clear error instead of
failing silently.

## Optional upgrade: Clerk
If you outgrow the built-in auth later - need more social providers
(Google, etc.), managed user management UI, or org/team features - Clerk
is a drop-in replacement. It needs its own account and keys the same way
GitHub OAuth does. The rough shape of that migration:

1. Sign up at https://clerk.com, create an application
2. `npm install @clerk/nextjs` in `frontend/`, wrap `app/layout.tsx` in `<ClerkProvider>`, add `frontend/middleware.ts` with `clerkMiddleware()`
3. On the backend, verify Clerk's JWT (via its JWKS URL) instead of the JWTs this app currently issues itself - `app/api/deps.py` is the one place that would change
4. `User.id` would come from Clerk instead of being generated locally; everything else (the `user_id` scoping on `Review`/`Settings`) stays the same

Not necessary unless you specifically need what Clerk adds - the
current setup is already secure, working, self-contained auth.
