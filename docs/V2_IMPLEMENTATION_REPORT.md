# ShramLink V2 implementation report

V2 is based on verified MVP commit `92292c308f249efad593146fb8b635165445ed18`
in `Je37-arch/ShramLink`. Work is confined to `feature/hindi-voice-v2`.
No presentation was edited. No new framework, paid service or payment integration
was introduced.

## Retained and extended

- Flask application factory, Jinja, SQLAlchemy models, password authentication,
  role/ownership checks, CSRF, login throttling, secure session configuration and
  CSP. The 51 original backend/security tests remain intact.
- Shared recruitment operations: deterministic ranking, eligibility, duplicate
  protection, atomic capacity reservation and persistent application status.
- Worker/employer identity, industrial focus, navy/turquoise palette, bundled
  Hindi fonts, typed registration, typed profile editing and no-JavaScript forms.
- Original year columns and all legacy records. Inactive legacy payment schemas
  remain only for data retention; no active route depends on them.

## Replaced or new

| Component | Change and rationale |
| --- | --- |
| `voice-assistant.js` | Replaced manual microphone turns with an explicit session and turn manager. Clear answers advance automatically; only full review confirmation can save. |
| `profile-language.js` | Extracted bounded Hindi/Hinglish vocabulary, numbers, commands, corrections and exact duration parsing for independent tests. Unsupported/ambiguous answers request clarification. |
| `hindi-speech.js` | Shared Hindi-only voice discovery, picker, preflight, cancellation, short utterances and timeout protection for onboarding and discovery. |
| Experience storage | Added nullable `users.experience_months` and `jobs.min_experience_months`. `init-db` backfills only NULL values using legacy years × 12. No columns/records are removed. |
| Experience validation | Months are authoritative; legacy years remain accepted when months are absent. Conflicting units fail validation. Adult age/experience bounds remain enforced. |
| `/discover`, `discovery.js` | Authenticated one-job stack with equivalent pointer, keyboard and button actions. Existing applications are removed from the active stack. |
| Application confirmation | Right swipe and Apply open a modal. Only its affirmative button submits the existing CSRF-protected API request. Loading, timeout, server and stale-capacity failures are visible. |
| Skip recovery | Undo and restore use account-scoped tab storage containing job IDs only. No permanent rejection of opportunities. |
| `job_speech.py` | Builds summaries from stored fields, Hindi number words and recognised 24-hour time ranges. Full employer conditions have a separate read-aloud action. |
| Tutorial | Optional first-entry practice, replayable from Help. Sample gestures cannot reach application submission. Hindi speech is opt-in and every lesson has a Next button. |
| Worker UI | A dominant Find Work action, profile status, applications, large controls and fixed mobile Pause/Stop/Type controls. Employer forms/review now show exact month requirements. |

## Conversation safeguards

The session uses idle/speaking/listening/interpreting/paused/saving states and
preflight/answer/review/correction phases. It deliberately does not listen while
speaking. A 300 ms quiet gap follows synthesis; recognition results are interpreted
only after the recogniser's `onend`. Each callback belongs to one current turn.

- Recognition: 12-second turn limit; one automatic retry for silence per question.
- Unclear answers: pause after three failed interpretations on one question.
- Overall bounds: six accumulated clarification/silence failures or 80 turns pause
  the session. An explicit new Start resets the budget.
- Microphone shutdown: if `onend` does not arrive within 1.5 seconds, pause and
  block new speech/listening until shutdown is observed or the page is reloaded.
- Synthesis: Hindi candidates only, up to 2.5 seconds for delayed discovery,
  25-second timeout per short utterance, no automatic synthesis-error loop.
- Stop, typing, backgrounding and new turns invalidate stale callbacks. Pending
  button-driven restarts cannot override a later Stop.
- Final review is tied to a snapshot of the form. Editing clears confirmation;
  a resumed voice session reads the changed profile again before accepting save.

Names are kept in the recognised script, not guessed/transliterated. e-Shram is
optional, format-checked and self-reported. Account credentials remain typed.

## Discovery safeguards and tradeoffs

Only the marked strip inside each card consumes swipe input (`touch-action:none`).
The rest of the page scrolls normally. The strip excludes the outer 24 px browser
edges; gestures need at least 70 px movement, a 1.4 directional dominance ratio,
and 40–1600 ms duration. Cancelled/diagonal/short gestures do nothing. Arrow keys
operate only when the strip has focus. No gesture is the sole way to act.

Short summaries read actual role, title, employer, city, daily pay, date, shift,
exact minimum experience and the beginning of employer conditions. Truncated
conditions are disclosed, with a separate control to read the full requirements
and address. English or unusual free-text shift/condition content is retained
verbatim; it is not automatically translated or claimed to pronounce perfectly.
Changing cards or interrupting speech cancels the previous utterance sequence.
Automatic reading is opt-in and stops on backgrounding or a synthesis failure.

Matching remains the original explainable 50/30/15/5 ranking. No distance,
verification badge, probabilistic AI score or hiring guarantee is invented.
Selection remains an employer decision. Displayed completed years do not lower
eligibility: a 37-month requirement still rejects a 36-month worker.

## Data, privacy and release limitations

Tests use synthetic identities and temporary databases. No private database,
credentials, cookie files, transcripts or recordings are committed. Previous
credential-rotation instructions remain in README; V2 does not erase old Git
history or rotate an unrelated deployment's secret.

Back up and stop writers before upgrading. Code rollback should use a matching
backup/copy; concurrent V1/V2 writers would leave month data stale. SQLite is the
tested database. Skip history is tab-local, not synced between devices. Status
refresh is explicit; no push notification service was added.

Physical speech recognition, Hindi pronunciation, accessibility with a physical
screen reader, and mobile OS gesture behaviour still require device testing.
The reported Mac “question mark” defect was not reproduced on physical Macs here.
See `VOICE_COMPATIBILITY.md` and `V2_TEST_RESULTS.md` for precise evidence boundaries.
