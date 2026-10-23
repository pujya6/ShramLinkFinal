# ShramLink V2 test results

Run date: **2026-10-22 UTC / 2026-10-23 IST**. Development branch:
`feature/hindi-voice-v2`, based on verified MVP `92292c308f249efad593146fb8b635165445ed18`.

## Executed results

| Check | Actual result |
| --- | --- |
| Unmodified V1 backend/security suite | **51 passed** in 38.11 s |
| Unmodified V1 browser suite, isolated baseline source copy | **13 passed** in 100.47 s |
| Unmodified V1 Node parser suite | **3 passed** |
| V2 full Python suite, `python -m pytest -q` | **104 passed**, 0 failed, 0 skipped, in 257.64 s |
| V2 Node parser/gesture suite, `node --test tests/test_voice.js` | **28 passed**, 0 failed, 0 skipped |
| Ruff E4/E7/E9/F checks | Passed |
| Python compile checks and `git diff --check` | Passed |
| Documented startup | Repeated `init-db`, actual `python run.py` process and HTTP 200 passed using a fresh temporary SQLite database |
| Screenshots | Desktop/mobile landing, voice review, discovery, tutorial and both parties' selected application screens generated; landing, voice review, discovery and tutorial images visually inspected |

Runtime: Python **3.12.14**, Node **24.19.0**, Playwright **1.56.0**, headless Chromium
**141.0.7390.37**, SQLite on Linux. Dependencies and browser binaries had to be
installed in the fresh environment. The browser installer succeeded through its
alternate download host after the first mirror returned an invalid archive.

V2 Python breakdown: **51 retained backend/security tests**, **21 new month/
migration/description tests**, **15 adapted/extended V1 browser tests** and
**17 additional V2 browser tests**. The V1 browser microphone-tap expectations were
updated for the intentionally changed automatic-turn interface; the unmodified
V1 suite was run separately before changes. No failed test was removed to inflate
results. A silence test's clock setup was corrected during development so timers
were installed before starting recognition. A final test-only directory setup
makes screenshot tests runnable independently on a clean checkout.

## Acceptance evidence

| Criteria | Observed evidence | Limits |
| --- | --- | --- |
| One Start, full spoken onboarding | Chromium session: audio preflight → seven answers → review → affirmative save → reload and database read | Speech API events are simulated |
| Corrections, repeat, navigation | Name replacement, review rejection/correction, repeat, contextual optional skip; keyboard/visible recovery controls | Deterministic supported vocabulary, not open-ended Hindi understanding |
| No uncontrolled retries | Silence/timeouts, low confidence, ambiguous responses, permission/hardware/network/language errors, synthesis failures and global bounds | Browser callback simulation |
| Audio isolation | No synthesis/recognition overlap observed in the adapter; delayed/duplicate callbacks, missing `onend`, stop/pause/background and queued-restart races covered | Cannot establish real acoustic echo behaviour |
| Exact experience | All specified year/month examples, floor-year display, 36-vs-37-month eligibility, invalid/age-inconsistent inputs, V1 compatibility | Adult experience bound uses completed years of stated age |
| Safe migration | Missing month columns added; years and existing records preserved; repeated init does not overwrite 37/15-month values | SQLite tested; other databases unverified |
| Voice compatibility controls | Delayed voice discovery, multiple Hindi voice choice, English-only refusal, pronunciation sample, cancellation and timeout | No listener verified pronunciation |
| Discovery and tutorial | One active job; four simulated touch directions; real mouse drag, keyboard and buttons; optional practice cannot apply | Physical touch hardware/OS navigation unverified |
| Application safety | Modal confirmation, cancel, duplicate click/retry, already-applied exclusion, filled vacancy, network/500/CSRF errors; no false success | Real production concurrency/load not measured |
| Skip recovery | Undo, restore and same-tab reload preserve recoverability | No cross-device persistence |
| Spoken descriptions | Stored pay, city, role, shift, date and exact requirement; full conditions read separately; cancel/auto-read/fallback tests | Free text is not translated; physical pronunciation unverified |
| Typed and recruitment flows | JavaScript-disabled profile and application flow; mobile worker/employer registration, posting, application, selection and status after login | Tested in headless Chromium |
| Authorization and CSRF | Retained anonymous/role/ownership/CSRF tests; new discovery role test and live CSRF failure | Not an external penetration test |
| No active payment flow | Retained retired-route and user-facing content tests; applications/selections require no payment state | Historical unused schemas kept for data retention |
| Responsive/reduced motion | Layout checks at 320, 360, 390, 768, 1440 CSS px; reduced-motion tutorial test; screenshots inspected | Not physical-device accessibility certification |
| Repository boundaries | Development restricted to V2; publication ref checks recorded at release | No edits to the presentation or original repository |

## Reproduce tests and screenshots

From a clean checkout, after README setup:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium --only-shell
python -m pytest -q
node --test tests/test_voice.js
```

For the screenshots without running the full backend matrix:

```bash
python -m pytest -q tests/test_browser.py tests/test_browser_v2.py -k 'mobile_typed_recruitment or mocked_hindi_voice_all or desktop_landing or discovery_gestures_buttons or tutorial_practice'
```

The tests create local servers and synthetic temporary databases; do not point
these tests at a real deployment. Screenshots are generated under ignored
`test-results/`:

- `home-desktop.png`, `home-mobile.png`
- `v2-voice-review-mobile.png`
- `v2-discovery-mobile.png`, `v2-discovery-desktop.png`
- `v2-tutorial-mobile.png`
- `worker-selected-mobile.png`, `employer-selected-mobile.png`

Screenshots are viewport/rendering evidence, not evidence of actual audio. For a
modal screenshot, full-page capture shows the backdrop only over the viewport;
this is expected browser screenshot behaviour, not an unblocked live modal.

## Known failures and unverified behaviour

No automated failures remain in the executed full suite. Unverified items remain:

- Real Hindi microphone recognition, pronunciation and the reported two-Mac
  discrepancy; macOS/Windows/Android/iOS physical combinations.
- OS-specific microphone permission prompts, interruption/resume behaviour and
  real-device gestures; service/network behaviour outside the simulated cases.
- Field usability with low-literacy workers, screen-reader audits and production
  deployment/load. This release must not be described as certified or universal.
- Arbitrary job-text Hindi translation, unrestricted language understanding,
  offline speech, push notifications and cross-device skip history are not implemented.

Use `VOICE_COMPATIBILITY.md` for physical preflight. The original deployment's
credential rotation remains an operator task; deleting files from the branch tip
never erased their older Git history.

Protected refs checked before V2 publication: MVP `92292c308f249efad593146fb8b635165445ed18`; main `f7cd175570e76e0791d7b8b848b580b5b6ebbd39`. Only the new V2 ref is eligible for the release update.
