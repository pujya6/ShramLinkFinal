# Inside ShramLink — judge guide

Open `/inside` without logging in, or use the discreet How It Works link / footer link. It uses the established navy/turquoise style and a scoped stylesheet. The page is read-only and remains useful in V3b with no optional credentials.

## What to inspect

| Section | Actual implementation | Claim boundary |
|---|---|---|
| Speech/typing → interpretation | `voice-assistant.js`, `profile-language.js`, optional `interpretation.py` | Native speech events are mocked in automated tests; this is not physical accuracy evidence |
| Validation → saved profile | `validation.py`, existing profile routes and SQLAlchemy model | Worker confirmation is required; saved information is self-reported |
| Matching → discovery | `recruitment.matching`, active/date/capacity filters, `discovery.js` | Deterministic points, not an AI probability, distance measurement or hiring guarantee |
| Direct application | Existing authenticated/CSRF-protected internal workflow and employer ownership checks | Operates inside the demonstration environment |
| External preparation | `external_jobs.py`, signed snapshot, `DemoPreparation` | Local record only; no third-party application sender |
| Four configurations | Validated `VOICE_PROVIDER` and `JOB_SOURCE` switches | Requested/effective settings show configuration readiness, not successful provider connectivity |
| Duration illustration | The real bounded JavaScript parser | Input stays in browser memory; ambiguity produces clarification, no saved profile |
| Matching illustration | Eight fixed synthetic profiles passed to the real Python matcher | No real users/jobs queried, no provider calls or account changes |
| External preview illustration | Static, labelled synthetic example | Opening it creates no record at all |

All source/documentation links point to `Je37-arch/ShramLink`. The page does not display keys, transcripts, private worker data, database contents or administration endpoint paths. It never asks for a real phone number or identity document.

## Status wording

- **Implemented:** code and connected application behaviour exist.
- **Tested locally:** Flask/SQLite/backend or real headless Chromium interactions were executed locally.
- **Mock-tested:** browser speech callbacks/provider responses were simulated to test contracts, lifecycle and recovery.
- **Optional integration:** explicitly configured server-side; not required to use V3b.
- **Not yet verified on physical devices:** no actual phone/Mac voice quality claim, including the reported “question mark” problem.
- **Future roadmap:** genuine authorized external submission and independently verified credentials; neither is implemented.

The release evidence block is updated only from a completed test run. The protected V3 baseline count is labelled separately; it is not presented as newly executed release evidence. See [RELEASE_TEST_RESULTS.md](RELEASE_TEST_RESULTS.md) for exact counts and environment.

## Demonstrating the boundary

Change synthetic worker city from Delhi to Noida: ranking decreases but eligibility remains because city is a preference. Change the skill to Helper or experience to 18 months: the direct welder requirement is not met. Try “लगभग दो साल” in the duration example: it asks for clarification rather than guessing zero.

Open the external illustration. Emphasize that even a real demo preparation would have **Demo application prepared — not submitted externally** as its status. The illustration itself performs no POST and saves nothing.

Screenshots at 390×844, 768×1024 and 1440×1000 are under `docs/screenshots/release/`. Reproduce them with `python -m pytest -q tests/test_browser_release.py`; test images are written to ignored `test-results/`. These screenshots and simulated speech tests do not prove physical-device compatibility.
