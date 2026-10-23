# ShramLink release test results — 2026-10-23

Protected base: `0bea8e29aca12a2f48c08b9c748f6b7b6f127f33`. Release branch: `feature/shramlink-v3-release`.

## Execution status

**Final release run: 204 Python tests passed in 208.65 seconds; 41 JavaScript tests passed. Zero failures and zero skips.**

After recording these executed counts in the public evidence block, the three showcase viewport cases were rerun to regenerate and verify the displayed evidence. They are repeat checks, not additional cases added to the full-suite count.

Environment: Linux, Python 3.12, SQLite, Node.js 24, Playwright 1.56.0 and Chromium 141.0.7390.37. Real local Flask routes and browser controls are exercised. Microphone/synthesis callbacks and authenticated provider responses are simulated. All accounts, phone numbers, jobs and screenshots are synthetic demonstration data.

The protected V3 source was separately archived and rerun before edits: **175 Python tests passed in 175.21 seconds; 28 JavaScript tests passed**. These are baseline results, not the release count.

| Suite | Cases | Scope |
|---|---:|---|
| Retained V1/V2/V3 Python suites | 175 | Registration, recruitment, security, exact months, optional adapters, original browser/voice/gesture/tutorial behaviour |
| `test_release.py` | 16 | Fresh bootstrap, idempotence, refusal before legacy mutation, dates/history, both worker types, diagnostics, four-mode showcase and database recovery |
| `test_browser_release.py` | 10 | Three name-prefix cases through review/save/reload; seeded internal/external journey; new worker; skip recovery; judge page at three widths and without JS |
| `test_handoff_package.py` | 3 | Private-path exclusions, committed-source provenance, exact revision manifest and credential-pattern rejection |
| Release Python collection | 204 | 149 backend/packaging cases and 55 browser cases |
| `test_voice.js` | 41 | Existing 28 cases, 11 name cases, bounded correction/negation and optional-ID skip regression |

## What was reproduced

- The original parser returned `त झा`, `वन कुमार` and `तेन्द्र शर्मा` for the three confirmed name prefixes. The corrected parser preserves each complete name; original script and Roman name case remain intact.
- `init-db` alone creates zero jobs. Registering a non-demo worker before V3 seeding reproduces a safe seed refusal and zero demo fixtures. That is a reproducible explanation for the reported empty experience, **not proof of the user's exact database/configuration state**.
- Seeding first yields six direct cards, three eligible direct applications for the seeded welder/helper, and two external previews. An explicit welder/Gurugram filter yields zero cards. A construction-only/zero-month profile still sees the six direct cards, with zero eligible direct applications; eligibility is not a hidden discovery filter.
- Expiring all direct fixture dates hides those direct jobs, while the two external fixtures remain. Prior internal applications and external preparations are excluded; browser-session skips can independently empty the stack. The new explanations/recovery distinguish these situations.

## New release evidence

- Fresh, previously uninitialized nested SQLite path → guarded bootstrap → five accounts/six direct/two external records. Repeating does not reset the password or fabricate outcomes. CLI prints eight visible/three eligible direct, without printing the password.
- Legacy/non-demo databases are rejected before schema changes; stored data is unchanged. `SHRAMLINK_DEMO=false` refuses bootstrap. Expired unused ACTIVE dates refresh only by explicit flag; jobs with any application, filled/cancelled state or hires retain their history.
- A seeded worker browses eight cards, navigates, confirms one internal application and receives the employer's selected status. A freshly registered matching worker also sees the fixtures. External preparation persists with the exact non-submission status and no application POST outside the local app.
- Corrected names persist after final review/save/reload in a simulated Hindi voice conversation. Unclear/negative answers retain bounded dialogue handling and the optional e-Shram absence remains a skip.
- Judge page exercises the actual parser and matching function on synthetic inputs. It makes no provider requests, POSTs or database mutations. Requested/effective configurations remain distinct and only safe configuration labels are rendered. It is readable without JavaScript.
- Showcase screenshots and overflow/touch-target checks cover 390×844, 768×1024 and 1440×1000. The existing mobile/desktop checks also remain in the regression suite. Physical touchscreen and pronunciation tests are not claimed.
- Local production-mode Gunicorn smoke: schema initialized twice, bootstrap invoked twice, `/healthz` and `/inside` returned 200, HSTS was present, restart retained five accounts/six direct/two external records and zero fabricated applications. No public TLS or Docker runtime was tested.
- `git diff --check` and fatal Python lint checks (`ruff check --isolated --select E9,F63,F7,F82 app tests scripts`) pass. Packaging inspects committed source only; the final ZIP includes a revision/content manifest and excludes runtime/private files.

## Failures found during this pass

Initial new tests had three test-fixture/assertion mistakes: a nonexistent CLOSED enum, conflicting legacy-year/exact-month fixture values, and a Hindi status assertion that did not match the existing Selected label. They were corrected without changing application contracts.

The first full release run was **202 passed, 2 failed**. It exposed a real parser regression: broad negative-intent matching intercepted the optional e-Shram skip phrase. Correction detection was restricted to a leading negative token and a specific regression was added. The other failure was the retained UI source guard rejecting the prohibited payment-feature word even in a negative statement on the new guide; the guide now uses neutral wording. Both original checks passed on focused rerun. The final execution status above supersedes that interim run.

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium --only-shell
python -m pytest -q
node --test tests/test_voice.js
```

For current-release screenshots, run `python -m pytest -q tests/test_browser_release.py`; images are emitted in ignored `test-results/`. Committed copies are under `docs/screenshots/release/`. The original V3 screenshot script and historical evidence remain intact.

## Explicitly unverified

Actual Hindi audio and recognition on the affected Mac, Android/iOS/Windows; real xAI requests/quality/latency/cost; relevant live NCR vacancy supply; PostgreSQL; Docker runtime; sustained/multi-instance load; public HTTPS hosting and host backups. No original-team branch was available for an actual conflict-resolution trial. Public deployment is no longer a handoff requirement. Historical credential rotation is an operator action, not a completed test.
