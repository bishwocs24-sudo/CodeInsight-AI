# Run the full stack without paid hosting

Docker Compose runs the frontend and API, PostgreSQL, Redis, the scan worker, its scheduler, and an HTTPS proxy on one Linux machine. Use a machine you already have or an [Oracle Cloud Always Free Ampere A1 VM](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm). On Oracle, select an Always Free-eligible shape and boot storage in your home region. One VM using 2 OCPUs and 12 GB RAM fits the current A1 allowance if you have that capacity available. An Oracle account may ask for card verification. Cloud capacity varies, and idle instances can be reclaimed.

## Start the stack

1. Install Docker Engine and the Compose plugin. Point a public DNS hostname you control, such as a free Duck DNS subdomain, to the host. Allow inbound TCP 80 and 443 so Caddy can obtain and serve a public HTTPS certificate. Restrict SSH to administrators. PostgreSQL and Redis have no published host ports.
2. From the `codeinsight-ai` directory in the release checkout, set the hostname and create the deployment settings file. This command generates different random values for the database password and token signing key. Use it only for the initial setup. Keep the resulting file private and retain it for restarts and upgrades.

   ```sh
   PUBLIC_HOSTNAME=your-hostname.example
   (set -C; umask 077; printf 'PUBLIC_HOSTNAME=%s\nPOSTGRES_PASSWORD=%s\nJWT_SECRET_KEY=%s\n' \
     "$PUBLIC_HOSTNAME" "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" > deploy/free.env)
   ```

3. Build and start the service, then check readiness.

   ```sh
   docker compose --env-file deploy/free.env -f compose.free.yaml up --build -d
   curl -fsS "https://$PUBLIC_HOSTNAME/ready"
   ```

4. Create an operator account. Password entry is interactive.

   ```sh
   docker compose --env-file deploy/free.env -f compose.free.yaml exec web \
     python -m app.core.create_operator you@example.com
   ```

5. Visit the HTTPS URL. Open the public sample review, or sign in and queue a real scan. Confirm a finding can be downloaded as SARIF. Database, queue, and HTTPS data use persistent Docker volumes. For a host you rely on, keep a database backup outside the VM.

## Optional integrations

The sample, Semgrep, and built-in static reviews require no Gemini key. AI-backed reviews are off by default. To opt in, use a Gemini project without billing enabled and a model currently covered by its free quota. Set `GOOGLE_API_KEY`, `GOOGLE_MODEL`, and `PR_AI_ENABLED=true` in `deploy/free.env`, then recreate the services. AI requests are subject to provider quotas and data terms.

For GitHub PR automation, follow [Review Automation](REVIEW_AUTOMATION.md). Use your HTTPS URL plus `/automation/github/webhook`. Supply the `GITHUB_*` settings from that guide in `deploy/free.env`, and use a Compose override to mount the GitHub App PEM read-only into the worker at the configured `GITHUB_APP_PRIVATE_KEY_FILE` path. Restart the stack with both Compose files. Keep the private key out of the build context and repo.

Public registration and user-submitted sandbox execution are disabled in this deployment. Built-in static scans do not execute user-submitted tests.
