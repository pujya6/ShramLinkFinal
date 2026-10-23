# ShramLink V2 implementation plan

Baseline verified from GitHub: `92292c308f249efad593146fb8b635165445ed18`
on `feature/hindi-voice-mvp`. All changes belong to `feature/hindi-voice-v2`.

1. Establish the unchanged baseline test results. Retain Flask, SQLAlchemy,
   authentication, CSRF, authorization and shared recruitment operations.
2. Add nullable month columns and a repeatable, non-destructive backfill from
   legacy years. Preserve old API payloads while new forms use exact months.
3. Extract deterministic Hindi/Hinglish parsing and a shared Hindi-only speech
   controller. Replace manual microphone turns with a cancellable, bounded
   conversation, audio preflight and explicit final review confirmation.
4. Add an authenticated single-card discovery page using the existing ranking
   and application service. Provide gesture/button/keyboard equivalents,
   confirmation, recoverable skips, accurate spoken summaries and a safe tutorial.
5. Simplify worker navigation and preserve the typed/no-JavaScript path. Run
   regression, lifecycle, migration and mobile browser tests; inspect screenshots.
6. Document actual results, device limitations, demo steps and defensible claims.
   Commit and publish only the V2 branch; verify baseline/main refs unchanged.

Physical Hindi pronunciation cannot be established by a mocked speech API.
The two-Mac defect remains a reported symptom until reproduced on those devices.
