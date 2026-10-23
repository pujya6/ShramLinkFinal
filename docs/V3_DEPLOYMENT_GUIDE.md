# V3 deployment readiness

**Status: prepared, not deployed. No public HTTPS URL is claimed. Publishing requires approval.**

## Proposed bounded deployment

Use a Flask-compatible container host with HTTPS termination and an attached persistent disk, one application instance and the Dockerfile in this branch. A single Gunicorn worker with four threads is enough for the hackathon demonstration. A platform that can only serve static files cannot host this Flask backend.

Choose the lowest suitable plan only after checking its current price and disk persistence. No hosting purchase, paid plan, account setup or deployment has been performed. Host-specific prices and provisioning were not verified here.

The deployment must attach a persistent disk at `/data`, writable by container UID 10001. `DATABASE_URL=sqlite:////data/shramlink.sqlite3` must refer to that disk. Never rely on an image/container filesystem or `/tmp` to preserve profiles. Multiple independent instances must not use disconnected SQLite copies. A PostgreSQL migration is future operational work, not a tested deployment path for this release.

## Environment

Required:

```text
SHRAMLINK_ENV=production
SHRAMLINK_DEMO=true
DATABASE_URL=sqlite:////data/shramlink.sqlite3
VOICE_PROVIDER=deterministic
JOB_SOURCE=demo
PORT=8000
```

Set a **new** random `SECRET_KEY` of at least 32 characters using the host's secret manager; do not paste it into a repository or Dockerfile. Optional provider settings remain server-side. Start with V3b and keep the API key absent until costs and physical voice behaviour have been checked.

The app rejects a production startup with a missing/short secret, no explicit database URL, or an in-memory database URL. The operator must ensure the secret is new; the app cannot detect historical compromise. It sets Secure, HttpOnly, SameSite=Lax cookies and HSTS. Keep the origin behind the HTTPS reverse proxy; do not expose an alternate public HTTP application endpoint. The internal `/healthz` check can use HTTP and requires no login.

## Build, initialize, start

Before deploying, stop writers and back up any existing database. The operator runs the migration in a one-off container/shell with the same secret environment and persistent volume:

```bash
python -m flask --app run.py init-db
python -m flask --app run.py seed-demo-v3
```

The seeder prompts for an operator-chosen demonstration password and refuses non-demo user data. Run it once on an isolated database before registering ordinary demonstration participants. Never seed a genuine production user database. It creates no application/selection outcomes.

Production command without Docker:

```bash
gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 30 run:app
```

The Dockerfile uses that command, installs only runtime requirements, runs as a non-root user, copies only application assets and checks `/healthz`. Docker image build/run has not been executed in this environment because Docker is unavailable. Validate volume ownership and image build on the chosen host before publishing.

Do not run Flask's development server as the public service. Do not run migrations automatically from every worker at boot. `/healthz` returns 503 if the database/schema is unavailable and 200 when ready; it exposes no credentials, counts or provider details.

## Optional services and costs

- Enable xAI only after setting a provider billing cap and checking the currently supported `grok-4.3` model and token prices. Default limits: 60 attempted calls/day globally, 30/day/worker and eight/minute/worker. Failed/time-out calls count toward the local cap and may still incur provider charges.
- Set both daily request limits to 0, or use `VOICE_PROVIDER=deterministic`, to disable paid interpretation.
- `/admin/service-status` reports counters and an optional cost estimate from configured prices and reported tokens. It is not a complete billing ledger.
- Greenhouse retrieval is public GET only, capped at one request per 15-minute bucket and 48 attempts/day/board. No external application credentials or sender are implemented.
- See [configuration](V3_CONFIGURATION.md) for privacy, schema checks, caching and fallbacks.

## Pre-publication checks

1. Rotate credentials previously committed in repository history. Use a fresh session secret; reset any compromised account passwords and service credentials. Deleting current files does not erase history.
2. Verify an HTTPS URL with a valid certificate, secure cookies, CSRF rejection, worker/employer role denial and no debug traceback.
3. Register a synthetic worker, complete typed onboarding, post a direct vacancy, apply and select. Restart the deployed instance; verify both accounts retain the status.
4. Run audio preflight on the actual demonstration phones/Macs. Microphone access needs HTTPS or localhost. Test denial, no Hindi voice, silence, stop/pause and typing. The reported Mac pronunciation defect remains unverified.
5. Practise tutorial audio from its visible Listen button. Replay, stop and close must cancel cleanly. Check original and monthly pay units on discovery, confirmation and employer pages.
6. Prepare an external demo application. Confirm the permanent local-only notice and exact non-submission status. Inspect network traffic to ensure no application POST leaves ShramLink.
7. Review access logs, retention, disk backup and rate counters. Do not log request bodies, transcripts, cookies or API authorization headers.

## Backup and rollback

Use the SQLite backup API or stop all writers before copying the database. Test a restore on a separate path. A persistent disk alone is not a backup.

Roll back to V2 only with the **pre-V3 database snapshot**. V2 cannot represent new monthly pay or external preparation records. Keep the original baseline commit recoverable; do not force-update its branch.

## Actual local readiness evidence

Gunicorn was started in production mode using a temporary on-disk SQLite database, initialized twice and seeded once. `/healthz` returned 200 with HSTS. After terminating and restarting Gunicorn against the same path, health returned 200 and all five fictional accounts, six direct jobs and two external fixtures remained; there were no fabricated applications. This validates the local command/restart path, **not** public hosting, TLS termination, Docker build or physical microphone compatibility.
