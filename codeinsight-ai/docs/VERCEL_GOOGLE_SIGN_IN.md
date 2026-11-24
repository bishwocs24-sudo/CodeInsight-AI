# Google sign-in and saved reviews

The hosted site signs in with Google at `/login/` and opens `/workspace/` after authorization. The public scanner at `/scan/` works without credentials.

1. In the Google Cloud project, enable the Google Drive API. Configure the Google Auth Platform branding, audience, and consent information. If using the external testing audience, add the accounts that will test the site.
2. Create an OAuth client of type Web application. Register `https://codeguard-ai-demo.vercel.app/api/auth/callback/google` as an authorized redirect URI. Request openid, email, profile and `https://www.googleapis.com/auth/drive.appdata`.
3. In Vercel Production, save the client ID as `AUTH_GOOGLE_ID` and the client secret as `AUTH_GOOGLE_SECRET`. Use the existing `AUTH_SECRET`. Set `AUTH_URL` to the production origin if Vercel does not provide the canonical hostname.
4. Redeploy, complete sign-in, run a scan and choose Save report. Open the report from history and export it as SARIF. Confirm a separate Google account sees its own history.

Reports are stored as individual snapshots in the user's Google Drive application data folder when the user chooses Save report. They include the filename, diagnostics, dispositions and relevant source excerpts. Scanning does not store the full input file. Server-side requests use the access token in the encrypted session. When authorization expires, sign in again.

Run hosted workspace checks from the frontend directory with `node --test tests/google-workspace.test.mjs`. Background Semgrep and PR automation use the separate worker stack described in REVIEW_AUTOMATION.md.
