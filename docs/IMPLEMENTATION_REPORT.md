# ShramLink MVP implementation report

Scope: `Je37-arch/ShramLink`, `feature/hindi-voice-mvp`. Baseline: `f7cd175`.
Prepared 23 October 2026 (Asia/Kolkata). The presentation is unchanged.

## Retained

- ShramLink name, hard-hat/industrial identity, Hindi worker focus and factory
  recruitment concept, using the supplied navy/turquoise direction.
- Flask application factory, Jinja templates, SQLAlchemy, Flask-Login, password
  hashing, blueprint layout and the existing users/jobs/applications relationships.
- Original role, skill, job and application enums; unique worker/job application
  constraint, status timestamps and employer ownership relationship.
- Historical verification, ratings, mass-hire and payment storage definitions.
  No migration drops tables, removes columns or rewrites existing records.
- Browser-native SpeechRecognition and SpeechSynthesis as the voice mechanism.

## Rewritten or repaired

| Component | Reason and resulting behaviour |
| --- | --- |
| `static/js/voice-assistant.js` | Inspected before replacement. Previously a navigation-command widget with no registration save flow, unsafe transcript HTML, unbounded voice loading and recognition restarts. Now a finite question → answer → correction/confirmation → review → save flow, with safe text rendering and explicit microphone sessions. |
| Authentication | Removed shared demo OTP, auto-verified workers and remembered default logins. Uses individually chosen hashed passwords, session renewal, inactive-user checks, legacy credential lockout and HMAC-keyed DB-backed login limits. Worker phone numbers remain unverified identifiers. |
| Recruitment routes | Removed escrow calculations/gates and fabricated distance/payment metadata. Shared validated operations now drive HTML and JSON: vacancy → application → shortlist/select/decline. |
| Selection | Atomic vacancy-capacity update and conditional application transition in one transaction. Repeated requests cannot increment hires twice. Selected/rejected decisions cannot silently flip. |
| Profile persistence | The same server validation/save operation handles typed forms and the voice-filled form. Confirmation is required. Optional ID is self-reported, never a verified badge. |
| Database setup | Explicit repeatable SQLite initializer replaces automatic app-start table creation and broad fake-data seeding. Additive upgrades lock legacy credentials without deleting their records. |
| UI | Replaced affected prototype screens and disconnected standalone dashboard with real database-backed flows; added local CSS/fonts, large controls, labels, focus states and useful empty/errors/loading states. No new frontend framework. |

## Removed from the active application

- Escrow, automatic payout and payment-gateway claims, payment dashboards/actions,
  mass-dispatch placeholders, fabricated earnings, kilometre distances and ratings.
- Duplicate login route, unused demo-data module and standalone mock dashboard.
- Unused JS/templates that referenced removed capabilities and missing assets.
- Tracked `.env`, cookie files, compiled Python caches and database from the branch
  tip. The local database and sensitive originals were retained privately.
- Unused Flask-Migrate dependency; there was no migration history to reuse.

## New

- Seven-question Hindi onboarding, including preferred domain, experience and city;
  typed fallback works without speech APIs or even JavaScript.
- Profile editing; review before save; optional-ID skip; spoken repeat, previous,
  correction and explicit review confirmation; bounded silence/synthesis timeouts.
- Server-enforced field validation, CSRF on every mutation, active-account and role
  guards, employer ownership checks, safe error responses and security headers.
- Explainable 100-point rule-based ranking and explicit skill/experience eligibility.
- Employer applicant status filter, shortlist/select/decline, shared persistent status.
- Explicitly labelled demo accounts with an operator-selected password; no shipped
  credentials. Operator-only password reset invalidates existing sessions.
- Asia/Kolkata business dates and local, licensed Hindi/Latin fonts.
- Automated integration/security/browser tests and focused Node speech parser tests.

## Security and data-preservation boundaries

The original environment file contained session-secret/debug configuration. Its
values and cookie/database contents were not included in the handoff. The new
application no longer uses the tracked key or shared OTP. Production requires a
fresh secret; existing deployed installations must still rotate their exposed
secret and affected credentials. Removing the latest files does not erase history.
No Git history rewrite, `main` change or upstream repository write was performed.

Legacy credential version 1 is assigned only when adding that column to an old
database. Fresh accounts receive version 2. Password resets increment the version,
invalidating signed sessions for the previous version. Existing verification flags
remain stored but cannot produce a verified claim in this MVP.

Optional ID entries are ordinary private database text, not independently validated
or encrypted at rest. Employers receive only an ID-provided indicator. Filesystem
and backup access must be restricted. No audio or transcript logging was added.

## Validation and remaining work

See [TEST_RESULTS.md](TEST_RESULTS.md) for the acceptance matrix, actual test counts
and explicitly unverified behaviour. See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the
presentation sequence and [PRESENTATION_CLAIMS.md](PRESENTATION_CLAIMS.md) for bounded
claims. Physical microphone/Hindi voice compatibility is the outstanding P0
acceptance demonstration; browser event tests do not substitute for that check.

Deferred: government/business credential integrations, SMS delivery, self-service
account recovery, worker ratings, administrator verification, notifications,
attendance, multi-day scheduling, cancellation/reversal workflows and large-scale
search. These are not represented as implemented features.
