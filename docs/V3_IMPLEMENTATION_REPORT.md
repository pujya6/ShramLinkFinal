# ShramLink V3 implementation report

## Scope and baseline

One configurable Flask application on the existing `feature/shramlink-v3` branch. The branch started at the verified V2 commit `06f83a2f6f25eee607922a12b53712a5d97b2907`. The protected V2, MVP and main branches and the original team's repository are outside the write scope. The pitch deck is untouched.

## Retained

- ShramLink brand, worker/employer roles, Delhi–NCR industrial skill catalog, local Devanagari fonts, navy/turquoise identity.
- Flask, SQLAlchemy, Jinja and vanilla JavaScript; authentication and typed/no-JavaScript paths.
- V2 bounded dialogue, Hindi voice discovery, pronunciation preflight, microphone/TTS separation, cancellation tokens, silence/error limits, corrections and explicit profile review.
- Exact experience months, age/experience validation, deterministic ranking, application uniqueness, ownership checks, CSRF and atomic capacity reservation.
- Historical database records, including inactive legacy payment storage. No payment workflow was reintroduced.

## Redesigned

The common interface was rebuilt before optional integrations. New page structure replaces the old broad hero/form layouts: a dedicated worker entry card beside a separate employer entry; compact icon-led three-step journey; a conversation stage with a large state indicator and editable profile dock; a dashboard dominated by Find Work with a useful profile summary; and a job card with a prominent navy pay/location block. Employer forms now explicitly select employment type and pay period.

The shared stylesheet was replaced and organized around these layouts, responsive breakpoints, visible focus, 44px minimum buttons, reduced motion, plain Hindi and local fonts. Icons are small source SVGs, not a new asset dependency. The typing form remains available, opens automatically on unsupported browsers/errors and has a no-JavaScript fallback.

Before/after captures cover landing, onboarding, dashboard and discovery at 390×844, 768×1024 and 1440×1000. All were visually inspected. The screenshot script uses temporary synthetic accounts. During review, a typing button hidden after voice errors and a monthly-pay label on the employer applicant page were found and repaired. See the [gallery](screenshots/index.html).

## New data and recruitment behaviour

- Additive job columns: employment category, exact pay amount, pay unit and fixture key. Old categories remain unknown; monthly pay is never converted to a made-up daily rate.
- `ExternalVacancy` holds read-only public/fictional source snapshots. `DemoPreparation` stores a separate worker-confirmed local preview; it has no Applied/Selected/Hired state and no submission client.
- External preview shows the source URL, saved profile facts, deterministic matching reasons and missing/unknown information. A signed 15-minute confirmation binds the worker, current profile and current vacancy. Changing data invalidates the confirmation. Repeated requests create one record.
- `seed-demo-v3` adds six fictional direct jobs across four fictional employers and two fictional external opportunities. All are labelled; no outcomes are seeded. It refuses non-demo databases and preserves existing data on repeat runs.

## Optional adapters and shared modes

Validated environment switches select V3a–V3d. All share templates, data, authentication and internal recruitment. Missing configuration falls back to V3b components. Mode indicators appear only for demonstration accounts/admins; no worker configuration controls exist.

Greenhouse is a read-only public Job Board adapter with strict host/token checks, sanitized text, source URLs/timestamps, five-second socket timeout, response bounds, database refresh quotas and 24-hour stale visibility limit. Only explicit supported industrial job titles in NCR are imported; missing fields remain missing. Formal categorization requires an explicit operator attestation and is still labelled unverified. One live public board fetch succeeded with 20 posts and zero supported matches. Another candidate was unavailable. No live relevant vacancy is claimed.

xAI uses the documented Responses API and `grok-4.3`, reasoning disabled, no tools, `store:false`, strict structured output and local schema/field validation. Known local parses remain authoritative. Only unresolved short answers go to the adapter. Fixed Hindi clarifications replace arbitrary model instructions. Nothing can save or hire without the existing user confirmation/authorization. Request quotas, response limits, cancellation and counter-only usage metrics are implemented. No xAI credential was available; genuine cloud behaviour and costs are unverified. No paid requests were made.

## Tutorial audio investigation

V2 auto-opened the tutorial silently and used the Listen control as an audio toggle: after playback, pressing it again could simply turn the toggle off instead of replaying. That is a plausible UI cause of a perceived missing replay, not proof of the physical-device root cause.

V3 has a clear Listen/Replay control and a separate Stop control. The first explicit click enables narration of subsequent lessons; auto-opening alone never plays speech. Each lesson can replay, stop, skip or advance with a button. Stale speech results cannot overwrite a new lesson's status. Missing voices/synthesis errors leave visible practice and navigation. Browser simulations verify these behaviours. Physical audio quality remains to be tested.

## Security and operational readiness

Existing security contracts remain. New external routes require a completed worker profile, role authorization, CSRF for mutations, signed confirmation and unique records. Provider credentials stay on the server. Fixed endpoints reject redirects; no external application request method exists. Metrics contain counts only, not transcripts. Preview snapshots omit phone, email and e-Shram ID.

A database-backed health endpoint, production Dockerfile, explicit persistent-database requirement and deployment guide are added. Local Gunicorn restart/persistence smoke checks passed. No public site was deployed, no hosting costs were incurred and no Docker image was tested. Historical exposed credentials still require operator rotation before public use.

## Limitations and tradeoffs

- Native Hindi recognition and pronunciation depend on the browser/device/vendor service. All automated speech is mocked; the affected Mac, Android and iOS remain unverified.
- xAI semantic interpretation may be wrong even when schema-valid. Worker readback and final review remain essential. No live authenticated xAI call or monetary billing behaviour was verified.
- The supported industrial catalog and Greenhouse title filter are intentionally narrow. There may be no live relevant jobs. English external descriptions are not automatically translated.
- Source formality and employment terms are not independently verified; operator attestation is visible, not a badge of trust.
- SQLite deployment is limited to one persistent application instance. PostgreSQL migrations, Docker build and public HTTPS hosting remain unverified.
- Time-bucket service counters need a retention job for a long-lived service. No retention policy for real user data is claimed by this hackathon release.
- Older V2 code cannot correctly render V3 monthly vacancies. Rollback requires the matching pre-V3 database snapshot.

Test counts and demonstrated configurations are recorded in [V3_TEST_RESULTS.md](V3_TEST_RESULTS.md). Presentation wording is constrained in [V3_PRESENTATION_CLAIMS.md](V3_PRESENTATION_CLAIMS.md).
