# Deployment readiness — optional after integration

**No deployment is required for this handoff. Nothing has been provisioned, purchased or published.** There is no verified public HTTPS URL. This checklist is for the team if it chooses to host the reconciled release later.

## Hosting recommendation and limitations

A **paid Render Flask/Python web service with an attached persistent disk**, one instance and Gunicorn is a practical browser-dashboard option for a team without local tooling. The recommendation is based on this application's tested SQLite persistence and Flask runtime; it is not a completed hosting test or purchase recommendation at a quoted price.

| Option | Suitability for this release |
|---|---|
| Local laptop / existing college server | No new hosting subscription if hardware already exists; localhost supports microphone preflight, but is not a public service. Remote access needs team-managed HTTPS/storage. |
| Render Free web service | Useful only for a disposable preview. Its filesystem is ephemeral, it can idle down, and persistent disks and dashboard shell are unavailable. **Not suitable for preserving this SQLite demo across restarts.** |
| Paid Render web service + disk | Supports the persistent file and browser shell needed for bootstrap. Compute/storage incur charges; review current pricing and limits before choosing. One attached disk means one service instance. |
| Free hosted PostgreSQL workaround | Not a verified shortcut: this release's PostgreSQL migrations/runtime are untested, and Render's free Postgres currently expires after 30 days. Do not describe it as the supported persistence path. |

Official sources checked 2026-10-23: [Flask/Gunicorn deployment](https://render.com/docs/deploy-flask), [free limitations](https://render.com/docs/free), [persistent disks](https://render.com/docs/disks), [browser shell availability](https://render.com/docs/ssh), [current pricing](https://render.com/pricing). Exact current compute/disk prices were not reliably available in the retrieved pricing page and are not quoted here. No account or paid credentials are assumed.

## Browser-dashboard procedure if the team later authorizes hosting

1. Connect the team-approved integrated repository/branch as a **Web Service**, Python 3.12, build command `pip install -r requirements.txt`. Use manual deployment while validating the handoff.
2. Choose a paid instance only after accepting the displayed charge. Attach a persistent disk, for example at `/var/data`. Configure `DATABASE_URL=sqlite:////var/data/shramlink-demo.sqlite3`. A disk is available at runtime, not in the build/pre-deploy job; do not initialize it there.
3. Use a newly generated `SECRET_KEY` through the host's secret environment. Set `SHRAMLINK_ENV=production`, `SHRAMLINK_DEMO=true`, `VOICE_PROVIDER=deterministic`, `JOB_SOURCE=demo`, and both xAI daily quotas to `0`. Leave the API key and board settings absent.
4. For a first isolated install, the start command below initializes schema only, then serves the app. It never seeds accounts. Run one instance/one Gunicorn worker. Back up data and review migrations before subsequent release deployments.

```bash
python -m flask --app run.py init-db && exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 30 run:app
```

5. Set the health-check path to `/healthz`. Once the schema-only service is healthy, open the service's **runtime browser Shell** and run `python -m flask --app run.py bootstrap-demo`. Supply the chosen demo password at the hidden prompt. This order avoids a health-check/first-initialization deadlock; do not register participants before bootstrap.
6. Verify the provider's actual HTTPS URL, certificate, secure session cookies, profile persistence and full demo flow. Restart the service and verify records persist. **Only then** describe it as deployed. Perform real-device Hindi audio checks on that URL.

The existing Dockerfile is also retained, using a non-root user and Gunicorn with `/data`. Docker builds/runtime and host volume ownership have not been verified here. Do not change the mount path without changing the absolute database URL accordingly.

## Environment reference

| Variable | Default / requirement |
|---|---|
| `SHRAMLINK_ENV` | `development`; `production` requires a secret and explicit database URL, enables Secure cookies and HSTS |
| `SECRET_KEY` | Empty in template; private persistent generated key locally. Production requires operator-generated ≥32 characters. The app cannot detect historical compromise. |
| `DATABASE_URL` | Local default `instance/shramlink.sqlite3`; explicit absolute SQLite path on persistent storage for hosting |
| `SHRAMLINK_DEMO` | `true` permits explicit demo fixture commands; never auto-seeds or proves an existing database is safe |
| `VOICE_PROVIDER` | `deterministic` (default) or `api` |
| `JOB_SOURCE` | `demo` (default) or `integrated` |
| `XAI_API_KEY` | Empty; optional private server secret, never browser code |
| `XAI_MODEL` | Empty; set only to allowlisted `grok-4.3` after provider verification |
| `XAI_DAILY_REQUEST_LIMIT` | 60 by template; 0 disables. Maximum 240. Use 0 for handoff demos. |
| `XAI_USER_DAILY_LIMIT` | 30 by template; 0 disables. Maximum 240; separate fixed eight/minute/worker limit |
| `XAI_INPUT_USD_PER_MILLION`, `XAI_OUTPUT_USD_PER_MILLION` | 0 = unknown price, not free; optional operator-entered usage estimate only |
| `GREENHOUSE_BOARD` | Empty; validated public board token, not a URL |
| `GREENHOUSE_EMPLOYER` | Empty; actual reviewed source employer label |
| `GREENHOUSE_FORMAL_ATTESTED` | `false`; explicit operator review required before true, still not independent verification |
| `HOST`, `PORT` | Local development defaults `127.0.0.1`, `5000`; Gunicorn uses the host-assigned port/start command |

The bootstrap password is prompted, not an environment default. There are no shipped operational passwords. Keep the private `.env` outside version control. See [V3_CONFIGURATION.md](V3_CONFIGURATION.md) for payload bounds, timeouts, rate counters, feed caching and provider documentation.

## Pre-publication checklist

- [ ] Integrate on a reviewed branch and rerun the release tests. Do not deploy an unresolved merge.
- [ ] Rotate any credentials exposed in historical commits; use a fresh session secret and reset affected accounts privately.
- [ ] Use an isolated demo database with a persistent disk; do not point bootstrap at real worker data.
- [ ] Back up/restore-test SQLite consistently. A disk or disk snapshot alone is not a validated database backup.
- [ ] Keep one instance; never use disconnected ephemeral SQLite copies. Do not run schema initialization from every request/worker.
- [ ] Configure HTTPS termination at the trusted host proxy; expose no alternate public HTTP app port. Relative application URLs and production Secure/HttpOnly/SameSite=Lax cookies are retained. Do not add blanket trust of client-supplied forwarded headers. Any custom proxy setup needs host-specific verification.
- [ ] Verify `/healthz`: 200 with initialized/readable database, 503 when unavailable. UI/API database errors should be generic; inspect connection/disk permissions privately, never publish SQL/credentials in logs.
- [ ] Bootstrap before registering participants. Verify 6 direct, 3 eligible direct and 2 external previews for the fresh seeded worker, without filters/history.
- [ ] Run direct application → selection → reload, then external local preparation. Confirm no external application POST exists.
- [ ] Perform Hindi preflight, real microphone denial, Type, Pause/Stop and tutorial Listen/Replay/Stop on the actual devices.
- [ ] Keep paid interpretation off until provider billing caps, configuration and real behaviour are reviewed. Timeouts may still cost money; local token counters are not a complete bill.
- [ ] Check feed-unavailable fallback, no-live-match messaging and clear fictional labels.
- [ ] Recheck records after a host restart. Record the actual HTTPS URL and test date only when verified.

Operational recovery: missing schema → run `init-db`; empty demo → use the isolated bootstrap procedure; invalid environment → correct the named setting and restart; database permission/disk failure → repair privately and retry. Do not delete a database as a recovery shortcut. The error screen advises checking application status after service returns because a lost response does not prove a write failed.
