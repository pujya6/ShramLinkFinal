# ShramLink V3 — काम से जुड़ें। आगे बढ़ें।

A Hindi-first industrial employment demonstrator for Delhi–NCR. One Flask / SQLAlchemy / Jinja application, retaining the original worker–employer relationship, navy/turquoise identity and recruitment rules. No frontend framework migration.

**Release branch:** `feature/shramlink-v3-release` in `Je37-arch/ShramLink`.
**Protected V3 base:** `0bea8e29aca12a2f48c08b9c748f6b7b6f127f33`.

**Team handoff:** [Quick start](docs/QUICK_START_FOR_TEAM.md) · [Final handoff](docs/FINAL_HANDOFF.md) · [Merge guide](docs/MERGE_GUIDE.md) · [Changed files](docs/RELEASE_FILE_INVENTORY.md) · [New release tests](docs/RELEASE_TEST_RESULTS.md) · [Judge showcase](docs/JUDGE_SHOWCASE.md) · [Limitations](docs/KNOWN_LIMITATIONS.md) · [Deployment checklist](docs/DEPLOYMENT_CHECKLIST.md).

Open **`/inside`** for a read-only architecture guide and synthetic examples. The release fixes Hindi name-prefix parsing and adds guarded demo bootstrap/recovery. It adds **no database schema changes over V3**. Public deployment is not part of this integration handoff.
**Protected V2 baseline:** `06f83a2f6f25eee607922a12b53712a5d97b2907`.

**बोलें → काम देखें → आवेदन करें → स्थिति देखें**

- Redesigned worker/employer landing, dedicated conversation interface, saved-profile dashboard and one-job discovery cards.
- One-start Hindi onboarding with spoken corrections, exact experience months, final review, pause/stop and complete typing/no-JavaScript alternatives.
- Swipe up/down to move, left to skip, right to review an application. All gestures have buttons; skipped opportunities are recoverable.
- Explicit direct informal/formal categories, daily or monthly pay, internal applications and employer decisions.
- Six fictional direct vacancies and two fictional external opportunities, seeded explicitly in an isolated demonstration database.
- External opportunities support **local preparation only**. Their status is **“Demo application prepared — not submitted externally”**. There is no third-party application sender.
- Optional public Greenhouse vacancy retrieval and bounded xAI interpretation. Neither is required for the default demonstrator.

Skills, employment categories and identities are self-reported or source/operator claims, **not verified credentials**. No escrow, automatic payments, government verification, real SMS OTP, advanced AI matching or hiring guarantees.

## Install and run

Tested with Python 3.12 and SQLite. Use Python 3.10+.

```bash
git clone --branch feature/shramlink-v3-release --single-branch https://github.com/Je37-arch/ShramLink.git
cd ShramLink
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
export DATABASE_URL="sqlite:///$PWD/instance/demo-release.sqlite3"
export SHRAMLINK_DEMO=true
export VOICE_PROVIDER=deterministic
export JOB_SOURCE=demo
python -m flask --app run.py bootstrap-demo
python run.py
```

Open **http://127.0.0.1:5000**. On Windows use `.venv\Scripts\activate`. The app does not create tables, accounts or vacancies at startup. `python init_db.py` is an equivalent initializer.

The fresh bootstrap above initializes a **separate demo database** and the six direct/two external fictional jobs together, before registration. It reports **6 visible direct, 3 eligible direct, 2 external previews, 8 cards** for the seeded worker. `init-db` alone never adds vacancies. The old `seed-demo-v3` command remains available, but the guarded bootstrap is recommended for a fresh handoff demonstration.

If an existing database contains ordinary worker accounts, keep it intact and choose a new empty demo path. Never relabel accounts or delete data to bypass the guard. To explicitly renew expired, unused ACTIVE fixtures in an all-demo database, use `bootstrap-demo --refresh-unused-dates`; applied/filled/cancelled opportunities are preserved.

Enter a demonstration password at the hidden prompt; no default password exists. Accounts:

- `worker.v3@example.invalid`: completed welder/helper profile with exactly 32 months of experience.
- `employer1.v3@example.invalid` through `employer4.v3@example.invalid`: fictional employers. Employer 1 owns the Delhi welder/helper jobs; employer 2 owns the monthly Noida welder job.

Create a new worker account to demonstrate onboarding from the beginning. All fixture jobs visibly say DEMO. No hiring outcomes are pre-created. Seeding repeats safely without resetting passwords, dates, profiles or applications, and refuses databases containing non-demo accounts. Seed before registering fresh workers. For a new event with expired fixture dates, use a fresh isolated database; do not delete records from a shared database.

## Choose one configuration

Set the two server variables in your private environment and restart:

| Mode | `VOICE_PROVIDER` | `JOB_SOURCE` |
|---|---|---|
| V3a | `api` | `demo` |
| V3b — default | `deterministic` | `demo` |
| V3c | `deterministic` | `integrated` |
| V3d | `api` | `integrated` |

Missing optional configuration falls back to local operation. A demo-account/admin indicator and the public read-only judge page distinguish requested and effective configured modes. Workers have no configuration controls. A configured provider is not proof that a live request succeeded.

See [configuration and migration details](docs/V3_CONFIGURATION.md). The important variables are:

| Variable | Purpose |
|---|---|
| `SHRAMLINK_ENV` | `development`; `production` enables secure cookies and HSTS |
| `SECRET_KEY` | Development generates a private persistent key; production requires a new random secret of at least 32 characters |
| `DATABASE_URL` | Default private `instance/shramlink.sqlite3`; production requires an explicit persistent database path |
| `SHRAMLINK_DEMO` | `true` permits the explicit fixture command; never mix demonstrations with a production user database |
| `XAI_API_KEY`, `XAI_MODEL` | Optional server-only key and documented `grok-4.3` model; both required for API mode |
| `XAI_DAILY_REQUEST_LIMIT` | Global attempted requests/day; default 60, maximum 240; 0 disables |
| `XAI_USER_DAILY_LIMIT` | Attempted requests/worker/day; default 30; additionally 8/minute |
| `XAI_INPUT_USD_PER_MILLION`, `XAI_OUTPUT_USD_PER_MILLION` | Optional operator-set token prices for an admin estimate; 0 means unknown, not free |
| `GREENHOUSE_BOARD`, `GREENHOUSE_EMPLOYER` | Public board token and actual employer name |
| `GREENHOUSE_FORMAL_ATTESTED` | Explicit operator category attestation; default false; does not imply independent verification |
| `HOST`, `PORT` | Local server bind, default `127.0.0.1:5000` |

## Voice and experience

Browser recognition uses `hi-IN`; a deliberately chosen Hindi voice reads questions and jobs. Preflight asks whether it sounds clear. No appropriate voice, denied microphone, silence or service errors leave typing available. ShramLink stores no raw audio or transcript history. Browser recognition may use the browser vendor's online service.

In API mode, only answers the local parser cannot resolve may be sent as text to xAI after the user starts the disclosed conversation. The optional e-Shram question and final confirmation stay local. Outputs cannot save a profile, select a worker or execute an external application. Field validation, readback and explicit final confirmation remain mandatory.

Experience is stored in exact months. Below 24 months, display months; at 24+ months, display completed whole years. Extra months remain stored and determine eligibility. Profile validation allows ages 18–80 and experience acquired after age 18. Supported skill/city/domain choices remain bounded.

**Automated speech tests are simulations.** Real Hindi pronunciation, recognition, Android/iOS and the reported Mac “question mark” defect remain unverified on physical devices. See [voice compatibility](docs/VOICE_COMPATIBILITY.md).

## Recruitment and external preparation

Direct matching remains deterministic: skill 50, city 30, domain 15 and experience 5 points. Skill and exact minimum months must match before an internal application. Employer selection still enforces ownership, legal state transitions, unique applications and atomic vacancy capacity.

For external cards, visible matching uses saved profile facts and explicitly lists unknown/missing information. The worker reviews the source and confirms a short-lived, signed snapshot. A separate local record is created. It is never listed as an internal Applied/Selected application. Changing the profile or vacancy invalidates the old confirmation.

Greenhouse retrieval uses only the official public **GET** endpoint. The narrow adapter accepts supported industrial role titles in the six NCR cities. Missing pay, shifts and experience stay unknown. It does not infer a salary, convert monthly pay to daily pay, or classify engineering/sales roles as manual skills. Live imported cards and fictional fixtures retain different source labels. No application endpoint or provider application credential is implemented.

## Tests and screenshots

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium --only-shell
python -m pytest -q
node --test tests/test_voice.js
python scripts/capture_screenshots.py --label v3
```

Tests use temporary databases and fictional accounts. Browser tests exercise actual Flask routes in Chromium; speech and authenticated xAI responses are mocked. The screenshot script uses temporary synthetic accounts and does not save cookies.

[Before/after screenshot gallery](docs/screenshots/index.html) contains landing, onboarding, dashboard and discovery at 390×844, 768×1024 and 1440×1000. Full-page captures may extend below those viewports. [New release evidence and test limits](docs/RELEASE_TEST_RESULTS.md). Historical V3 evidence remains in [V3_TEST_RESULTS.md](docs/V3_TEST_RESULTS.md).

## Migration, security and deployment

Back up the database before running `init-db`. V3 adds nullable pay/category/fixture columns and separate external-vacancy, preparation and service-counter tables. Legacy years are still backfilled only when months are absent. Old unspecified job categories stay unspecified. Existing records and inactive payment tables are preserved; recruitment never depends on payment state.

Do not run V2 against new monthly V3 jobs: its old daily-wage field cannot represent monthly pay. Roll back code **and the pre-V3 database backup together**. See [migration instructions](docs/V3_CONFIGURATION.md).

Authentication, role guards, CSRF, password hashing, secure session settings, database login throttling, restrictive CSP, local fonts and no-store page responses are retained. Committed private files from earlier history still require credential rotation; removing files from a new commit does not erase history. Use a new `SECRET_KEY`, reset affected account passwords and rotate any previously exposed service credentials before any deployment. Never commit `.env`, session cookies, databases or personal information.

For optional hosting after integration, see the [release deployment checklist](docs/DEPLOYMENT_CHECKLIST.md) and retained [V3 deployment guide](docs/V3_DEPLOYMENT_GUIDE.md). `/healthz` checks database readiness. A production Dockerfile is provided. **No public deployment has been published or verified.** Approval is required before publishing.

## Release material

- [Implementation report](docs/V3_IMPLEMENTATION_REPORT.md)
- [Test results](docs/V3_TEST_RESULTS.md)
- [Configuration and migrations](docs/V3_CONFIGURATION.md)
- [Deployment guide](docs/V3_DEPLOYMENT_GUIDE.md)
- [Hackathon demonstration](docs/V3_DEMO_SCRIPT.md)
- [Truthful presentation claims](docs/V3_PRESENTATION_CLAIMS.md)

The six-slide presentation has not been edited. Historical V1/V2 reports describe those baselines, not the V3 release.
