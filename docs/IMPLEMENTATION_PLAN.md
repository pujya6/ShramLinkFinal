# Hindi voice MVP implementation plan

Scope: Je37-arch/ShramLink, branch `feature/hindi-voice-mvp` only.

Inspection baseline: `f7cd175`. No AGENTS.md is present. Retain the Flask
application factory, SQLAlchemy models, worker/manager roles, job applications,
password hashing, blueprint structure and ShramLink industrial workforce identity.

1. **Secure foundation and recruitment slice.** Replace shared-OTP authentication
   with per-account passwords; add CSRF, active-user/role/ownership checks,
   validation, additive database initialization, explicit demo seeding and tests.
   Remove payment-dependent actions while retaining historical tables/columns.
2. **Hindi onboarding.** Replace the inspected navigation-only voice widget with
   a bounded question/answer/confirmation flow. Keep browser SpeechRecognition
   and SpeechSynthesis, require explicit microphone activation, validate answers,
   allow correction/repeat/optional skip, and save through the same server path
   as the complete typed form. Test events using a clearly identified mock.
3. **Accessible makeover.** Rework affected templates using local CSS and vanilla
   JavaScript; use navy/turquoise branding, readable Hindi, large controls, mobile
   layouts, honest data/verification labels and useful empty/error states.
4. **Verification and handoff.** Run Flask integration/security tests and real
   Chromium UI flows; distinguish mocked speech events from unverified physical
   Hindi audio/device compatibility. Write setup, demo, limitations and truthful
   presentation claims. Leave the presentation unchanged.

Database preservation: untrack the committed database without deleting the local
copy. Default to a fresh private instance database. Explicit upgrades add columns
and tables only. Existing accounts require credential reset because their prior
authentication cannot be trusted. Do not rewrite history or touch main/upstream.
