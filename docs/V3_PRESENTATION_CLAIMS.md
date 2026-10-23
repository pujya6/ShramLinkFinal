# V3 presentation claims — inventory only, no deck changes

## Demonstrated in automated application/browser tests

| Safe claim | Evidence / boundary |
|---|---|
| One shared Hindi-first employment demonstrator with a substantially redesigned mobile/desktop interface | Four-page before/after screenshots at 390, 768 and 1440 px; real Chromium layout checks |
| One-start bounded Hindi onboarding, corrections and final confirmation | Native API lifecycle simulated in Chromium; not physical speech recognition proof |
| Complete typed onboarding and persistent self-reported profiles | Actual Flask/SQLite registration, reload and login tests, including JavaScript disabled |
| Exact month-based experience with consistent eligibility | Parsing, persistence, migration and boundary tests; completed years shown from 24 months |
| One-job cards, swipe/button/keyboard navigation, skip undo and confirmation | Real Chromium UI and pointer/keyboard tests; simulated touch events, not physical touch hardware |
| Hindi job summaries and replayable tutorial with a separate Stop control | Actual job-data summaries; synthesis simulated; device voice availability still matters |
| Direct informal/formal vacancies with day/month pay | Actual posting, rendering, speech text and application tests; category claims remain unverified |
| Internal worker applications and employer selection with shared persistent status | Actual recruitment integration, duplicate, authorization, CSRF and capacity tests |
| External demo preparation that sends nothing to the employer | Separate local records, explicit signed confirmation, exact non-submission status and no outbound submission client |
| Four server configurations with safe local fallback | V3a–V3d use shared routes/data; optional adapters tested through simulated provider contracts |

## Narrow live evidence

- The official public Greenhouse GET endpoint for the Impinj board returned 20 postings on 2026-10-23. **Zero** passed the NCR/supported-industrial-role filter. This demonstrates public retrieval, not a supply of suitable live jobs.
- A local production-mode Gunicorn instance started, passed `/healthz`, restarted and retained synthetic database records. This is not proof of public HTTPS deployment.

## Implemented but not verified with live provider/device credentials

- Bounded xAI `grok-4.3` Responses API interpretation with strict output validation, quotas, usage counters and fallback. No API key was available, no paid request was made, and live accuracy/latency/billing remain unverified.
- Physical Hindi STT/TTS on Android, iPhone, Safari, Windows and the reported affected Mac. The Mac “question mark” defect is not claimed fixed.
- Public HTTPS hosting, chosen-host storage/backup, Docker image runtime and production browser microphone permissions.

## Future features — do not present as implemented

- Genuine authorized submission to external employers/platforms.
- Verified identities, e-Shram/GST validation or certified skills.
- Advanced AI matching, distance estimates, guaranteed eligibility or hiring.
- Live relevant NCR vacancy coverage beyond the evaluated narrow public adapter.
- SMS OTP, payment gateways, escrow, automatic payouts, attendance or benefits administration.
- Unrestricted chatbot, arbitrary job search tools or model-controlled recruitment actions.

Suggested six-slide inventory, without editing the deck: worker access problem; redesigned Hindi interaction; tested direct recruitment journey; clear external demonstration boundary; shared configurable architecture and evidence; remaining physical/provider/deployment validation. Keep “demonstrated”, “mock-tested” and “future” labels visible.
