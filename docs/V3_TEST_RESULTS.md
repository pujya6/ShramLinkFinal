# V3 test results — 2026-10-23

## Result

**175 Python tests passed; 28 JavaScript tests passed. No failures or skips in the final runs.**

Environment: Linux, Python 3.12, Node.js 24, SQLite, Playwright 1.56.0 and headless Chromium 141.0.7390.37. Browser tests use an actual local Flask server and temporary databases. Speech APIs and authenticated xAI responses are simulated. Test accounts, vacancy data and screenshots are fictional.

Commands from the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium --only-shell
python -m pytest -q
node --test tests/test_voice.js
python scripts/capture_screenshots.py --label v3
```

The final Python run completed in 170.35 seconds. Counts include parametrized cases:

| Test file | Passed | Coverage |
|---|---:|---|
| `test_recruitment.py` | 38 | Original registration, profile persistence, vacancy validation, applications, employer decisions and capacity |
| `test_security_and_setup.py` | 13 | Original role/ownership boundaries, CSRF, sessions, login controls and initialization |
| `test_v2_months.py` | 21 | Exact experience months, legacy migration, eligibility and spoken job data |
| `test_browser.py` | 15 | Original mobile typed journey, speech failures, no-JavaScript registration and responsive layouts |
| `test_browser_v2.py` | 17 | One-start dialogue, corrections/review, cancellation, delayed voices, gestures, application errors and tutorial practice |
| `test_v3_core.py` | 22 | Mode validation, categories, monthly pay, fixtures, additive initialization, external preview and authorization |
| `test_v3_integrations.py` | 36 | Public feed contract/cache/filtering, API schema/errors/limits, bounded corrections and all four modes |
| `test_browser_v3.py` | 13 | External local preparation, tutorial audio replay/failure, API proposal/cancellation/correction and redesigned screens |
| **Python total** | **175** | **130 backend/integration cases + 45 browser cases** |
| `test_voice.js` | **28** | Hindi/Hinglish parsing, exact mixed durations, ambiguity and gesture intent |

The archived V2 commit `06f83a2f6f25eee607922a12b53712a5d97b2907` was separately tested before development: **104 Python tests and 28 JavaScript tests passed**. V2 remains recoverable. Its test files were retained; the old browser employer journey now selects the two newly required category/pay-period fields.

## Four configurations

| Configuration | Actual evidence | Remaining limit |
|---|---|---|
| V3a — API + demo | Shared recruitment, server settings, validated mocked extraction, correction, timeout/error and browser fallback tests | No authenticated xAI request; real interpretation quality, latency and billing unverified |
| V3b — deterministic + demo | Complete actual local worker/employer journeys, fixtures, exact months, UI and local external preparation | Speech lifecycle simulated; physical voice accuracy unverified |
| V3c — deterministic + integrated | Mocked successful import, missing values, cache expiry/failure and shared recruitment; one real official public GET succeeded | Real response had zero supported NCR industrial matches; no live relevant-job supply demonstrated |
| V3d — API + integrated | Both optional contracts exercised together through mocks, with unchanged direct recruitment | No combined live-provider demonstration |

Missing keys/board configuration returns the corresponding component to local operation. Invalid settings fail startup. Tests verify that ordinary worker pages do not expose mode controls/indicators, and only administrators can read usage metrics. A configuration label does not claim a successful provider connection.

## Release checks

- **Recruitment:** actual SQLite registration, profile reload/login, employer posting, worker discovery/application, selection and shared status. Duplicate requests and filled vacancies do not invent success. Monthly salary retains its exact amount/unit throughout employer, worker and spoken representations.
- **External preparation:** a separate local record requires worker authentication, CSRF, explicit confirmation and a signed current profile/vacancy snapshot. Repetition is idempotent; changed profiles, other users and inactive vacancies fail safely. The UI preserves **Demo application prepared — not submitted externally** and both demonstration notices. No external submission client exists; tests prohibit outbound calls during preparation.
- **API interpretation:** strict shape/type/field validation, quoted evidence, no direct profile mutation, rate budgets, limited payload/output, fixed clarification and deterministic fallback. Browser tests reject late proposals after pause and require review after corrections. These are contract simulations, not provider accuracy measurements.
- **Feed:** only explicit supported roles/cities and allowlisted HTTPS source links are accepted. Missing salary, shifts and experience remain unknown. Tests cover sanitized text, removed postings, bounded refresh, stale cache and unavailable-source fallback.
- **Tutorial:** each lesson can play, replay, stop and advance; auto-opening does not trigger speech. Practice cannot apply. Missing Hindi voices/synthesis failure retain visible instructions. Speech callbacks are simulated.
- **Interface:** all four target screens were captured and visually inspected at 390×844, 768×1024 and 1440×1000, before and after. Layout tests check overflow and primary button size. Existing 320/360 px checks also pass. See the [gallery](screenshots/index.html) and [capture instructions](screenshots/README.md). No physical touchscreen test is claimed.
- **Static checks:** `git diff --check` and Python fatal-error checks (`ruff check --isolated --select E9,F63,F7,F82 app tests scripts`) pass. These are not a comprehensive security audit.
- **Production command:** a local Gunicorn process ran with production settings and a temporary on-disk database, passed `/healthz` with HSTS, restarted and retained five fictional accounts, six direct jobs and two external fixtures. Initialization ran twice; no application/hiring outcomes were seeded. This is local persistence evidence, not public HTTPS verification.

## Live integration observations

The official Greenhouse public Job Board endpoint for `impinjexternal` returned 20 posts on 2026-10-23. Zero matched the supported NCR industrial-role filter. A Quince candidate request was unavailable. No third-party application was transmitted. Demo fixtures remain explicitly separate from live vacancies.

No xAI credential was available and **zero paid requests were made**. No monetary costs, live authenticated errors or real extraction accuracy were measured.

## Failures found and resolved

The first baseline browser attempt failed because Chromium was not installed. After installing the pinned browser, all baseline tests passed. The first redesigned UI run found two permission/hardware-error cases where the Type control was hidden; the controls were made persistent and both cases plus the final suite passed. Visual/data review also repaired an employer applicant page that still labelled monthly pay as daily.

## Unverified or outstanding

- Physical Hindi STT/TTS on Mac, Android, iOS and Windows; recognition accuracy, pronunciation, retroflex sounds and device gesture behaviour. The reported Mac “question mark” issue remains unresolved on the affected device.
- A genuine xAI call and billing/latency/semantic behaviour; provider-side spending caps must be configured before use.
- A live source with relevant NCR industrial vacancies; English source descriptions are not translated.
- Docker build/run, public HTTPS deployment, chosen-host persistent volume/backup and real production microphone permissions. No public site was published.
- PostgreSQL migration/runtime, multi-instance deployment, sustained load and long-lived counter/data retention.
- Historical credential rotation is an operator action still required before public use. Removing files does not remove secrets from Git history.

The pitch deck was not edited. Only `feature/shramlink-v3` is the release write target; V2, MVP, main and the original team's repository are protected.
