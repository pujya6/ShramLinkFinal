# Validation and acceptance results

Run date: 23 October 2026, Asia/Kolkata. Environment: Linux, Python 3.12,
SQLite, headless Chromium 141.0.7390.37 via Playwright 1.56.0, Node.js.

## Automated checks

| Suite | Result | What it verifies |
| --- | --- | --- |
| Flask integration/security/setup | 51 passed | Registration/login, confirmed profile persistence, vacancies/applications/selection, validation, idempotency, concurrent last-slot hiring, role/ownership/CSRF, disabled accounts, reset/session invalidation, legacy-data preservation and repeatable setup. |
| Real Chromium UI | 13 passed | Mobile worker/employer journey; mocked Hindi speech events through all profile questions and save; correction/repetition/skip; seven recognition errors; silence/late events; TTS/start failures; no-JavaScript profile completion; responsive layouts. |
| Node speech normalisation | 3 passed | Hindi numbers, names, supported skills/domains/cities and optional ID parsing. |

The speech tests deliberately replace browser speech APIs with a test adapter.
They do **not** prove microphone capture, real Hindi recognition accuracy or actual
spoken Hindi playback. Browser tests use real HTML/CSS/JavaScript, HTTP requests,
authenticated sessions and temporary SQLite databases for every other operation.
No live personal records are used.

Final combined run: `64 passed in 127.35s` from `python -m pytest -q`, followed
by `3 passed` from the Node suite. Python compilation, focused Ruff checks and
`git diff --check` also passed. A separate `python run.py` smoke check served the
landing, login, worker registration and voice-script URLs with HTTP 200.

## Acceptance matrix

| # | Acceptance criterion | Status and evidence |
| --- | --- | --- |
| 1 | Hindi-speaking worker completes onboarding by voice | **Partially verified.** Full question/answer/review/save path passes with simulated `hi-IN` speech events. Real speech and physical-device audio are **unverified**. |
| 2 | Complete onboarding without microphone access | **Passed.** Unsupported recognition and permission-denied paths, plus JavaScript-disabled typed form, save through the real server. |
| 3 | Correct wrongly recognised information before submission | **Passed with simulated speech.** Replace an answer, edit review fields, repeat a question and save the corrected name. Real recognition accuracy remains unverified. |
| 4 | Profile remains after reload/login | **Passed.** Server tests and real browser login/reload read the persisted profile. |
| 5 | Employer creates a vacancy | **Passed.** HTML browser flow and JSON validation tests. |
| 6 | Worker discovers and applies | **Passed.** Matching/filter tests and real mobile UI flow. |
| 7 | Employer reviews and selects | **Passed.** Employer UI and database tests; concurrent selections cannot overfill the last position. |
| 8 | Status updates persist | **Passed.** Worker/employer reads, refresh and login; duplicate requests remain idempotent. |
| 9 | Recruitment needs no escrow/payment | **Passed.** Full journey creates no payment records; no active payment routes/claims. Historical schema is retained only for preservation. |
| 10 | Unauthorized operations are blocked | **Passed for tested cases.** Anonymous, wrong-role, other-employer ownership, missing CSRF and inactive sessions; this is not a penetration-test certification. |
| 11 | Mobile-sized viewport works | **Passed in Chromium.** Full journey at 390×844; public pages checked at widths 320, 360, 390, 768 and desktop 1440. Screenshots visually inspected. Physical Android/iOS remain **unverified**. |
| 12 | Documented startup works | **Passed locally.** Dependencies installed; explicit initializer and application factory started, HTTP pages served and tests ran. External hosting remains **unverified**. |

## Browser/device limitations

- Real microphone access, Hindi voice availability, speech quality in noisy factory
  environments, accents and network-dependent recognition: **unverified**.
- Physical Android/Chrome, iPhone/Safari, Firefox and Edge: **unverified**. Feature
  detection and typed fallback exist; equivalent speech support is not asserted.
- Browser speech may contact a vendor-hosted recognition service. No offline or
  on-device speech claim is made.
- Screen-reader review, comprehensive WCAG audit, load testing, production hosting,
  HTTPS reverse-proxy behaviour and non-SQLite databases: **unverified**.
- Mobile account creation still requires typed phone/password credentials. Voice
  assistance covers the profile, not password entry or verified mobile ownership.

## Deliberate MVP limits

Six supported skills, four domains and six Delhi-NCR city choices. Matching uses
city equality, not geolocation or a measured distance. Vacancy posting represents
a dated shift, not a full scheduling system. Status is refreshed on page load or
with the Refresh control; no push notifications. Decisions are final after
selection/rejection; cancellation/reversal is deferred. There is no government
verification or self-service recovery; operator reset requires identity checks
outside the application. Unsaved voice drafts do not persist across reloads.

The committed database, environment and cookies remain in historical Git commits.
Any old deployment still requires secret/password rotation; the branch changes
cannot perform that rotation on an inaccessible deployment.

## Reproduce

Use the README's dependency and browser installation commands, then:

```bash
python -m pytest -q
node --test tests/test_voice.js
```

Generated screenshots are in the ignored `test-results/` directory. The initial
browser CDN returned unusable archives; Playwright's alternate download source
successfully installed the tested Chromium headless shell. No browser tests were
reported as passed while browser installation was unavailable.
