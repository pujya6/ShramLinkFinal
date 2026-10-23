# Feature inventory for the later six-slide presentation

This is an inventory and proposed evidence order, **not an edited presentation**.

| Suggested slide | Claims that match the implementation | Evidence |
| --- | --- | --- |
| 1 · Problem and audience | ShramLink is a Hindi-first recruitment MVP for informal industrial workers and factories in Delhi-NCR. | Separate worker/employer entry points and regional city choices. Avoid unsupported market-size statistics. |
| 2 · Worker experience | A bounded Hindi voice-assisted profile flow asks name, age, skills, preferred domain, experience, city and optional e-Shram ID. Answers can be repeated, edited and confirmed. | Web Speech implementation; automated simulated-speech tests. Actual device/audio demonstration still needs a preflight. |
| 3 · Accessible fallback | The same profile can be completed through typing, without microphone access; the full server-rendered form works without JavaScript. | Real Chromium tests for unsupported recognition, denial/error recovery and JavaScript-disabled completion. |
| 4 · Recruitment journey | Employers post wage/skill/location/requirements; workers discover and apply; employers review and select; both accounts see persisted status. | Real browser journey plus database integration tests and reload/login verification. |
| 5 · Transparent matching and trust | Explainable skill/city/domain/experience ranking; self-reported profiles; format-only optional e-Shram entry; role and ownership authorization, CSRF and secure password handling. | Ranking breakdown, UI labels and negative authorization/validation tests. No claim of complete security certification. |
| 6 · Demonstrated MVP and next steps | Flask/SQLite/Jinja application, responsive desktop/mobile layouts, local Hindi fonts and documented setup; no paid AI API required. Next: physical-device Hindi speech trials and user testing. | Automated test report and demo script. Mobile viewport testing is not physical-device certification. |

Safe short feature list:

- Hindi voice-assisted onboarding with review and correction.
- Complete typed fallback and database-persisted profiles.
- Employer vacancy posting and worker applications.
- Shortlist/select/decline with shared application status.
- Deterministic, explainable matching and city/skill filters.
- Profile editing, applicant status filters and responsive UI.
- Password-based accounts, CSRF protection and authorization checks.

Do **not** claim: escrow-backed wages, automatic payouts, integrated payment
processing, guaranteed or increased wages, AI-driven matching, government-verified
identities/skills/factories, real SMS/Aadhaar OTP, e-Shram integration, attendance or
completion verification, automatic replacements, measured reductions in hiring
latency, rated workers, offline speech recognition, universal browser support or
production readiness. Those mechanisms/results have not been implemented or proven.
